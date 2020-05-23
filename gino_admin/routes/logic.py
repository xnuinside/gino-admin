import uuid
from collections import defaultdict
from copy import deepcopy
from csv import reader
from random import randint
from typing import List, Optional, Text

import asyncpg
from gino.declarative import Model
from sanic.log import logger
from sanic.request import Request
from sanic.response import HTTPResponse
from sqlalchemy.sql.schema import Column
from sqlalchemy_utils.functions import identity

from gino_admin import config
from gino_admin.utils import (CompositeType, correct_types, reverse_hash_names,
                              serialize_dict)

cfg = config.cfg


async def render_model_view(request: Request, model_id: Text) -> HTTPResponse:
    """ render model data view """
    columns_names = cfg.models[model_id]["columns_names"]
    model = cfg.app.db.tables[model_id]
    query = cfg.app.db.select([model])
    rows = await query.gino.all()
    output = []
    for row in rows:
        row = {columns_names[num]: field for num, field in enumerate(row)}
        for index in cfg.models[model_id]["hashed_indexes"]:
            row[columns_names[index]] = "*************"
        output.append(row)
    output = output[::-1]
    _response = cfg.jinja.render(
        "model_view.html",
        request,
        model=model_id,
        columns=columns_names,
        model_data=output,
        unique=cfg.models[model_id]["key"],
    )
    return _response


def process_csv_header(model_id, row, request):
    composite = False
    header = [x.lower().strip().replace("\ufeff", "") for x in row]
    if ":" in header[0]:
        composite = True
    if not composite:
        columns_names = cfg.models[model_id]["columns_names"]
        hashed_indexes = cfg.models[model_id]["hashed_indexes"]
        hashed_columns_names = [columns_names[index] for index in hashed_indexes]
        validate_header = deepcopy(header)
        for _num, name in enumerate(validate_header):
            if name in hashed_columns_names:
                validate_header[_num] = name + "_hash"
            if name not in columns_names:
                request["flash_messages"].append(
                    (
                        f"Wrong columns in CSV file. Header did not much model's columns. "
                        f"For {model_id.capitalize()} possible columns {columns_names}",
                        "error",
                    )
                )
                return request, None, composite
    return None, header, composite


def extract_tables_from_header(header: List, request: Request):
    header_columns = []
    tables_indexes = defaultdict(lambda: {"start": None, "end": None})
    for num, column_name in enumerate(header):
        column = {"table": None, "column": None}
        splitted_name = column_name.split(":")
        if ":" not in column_name or len(splitted_name) == 1:
            request["flash_messages"].append(
                (
                    f"Errors: Wrong Header in Composite CSV File. "
                    f"Column names in Composite CSV must be like 'table_name:column_name'. "
                    f"You set: {column_name}",
                    "error",
                )
            )
            return request, False
        table_name, _column_name = splitted_name[0], splitted_name[1]
        if table_name in cfg.models:
            column["table"] = (table_name, table_name)

        elif table_name in cfg.composite_csv_settings:
            column["table"] = (
                table_name,
                tuple(
                    [
                        model.__tablename__
                        for model in cfg.composite_csv_settings[table_name]["models"]
                    ]
                ),
            )

            if (
                "type_column" in cfg.composite_csv_settings[table_name]
                and _column_name
                == cfg.composite_csv_settings[table_name]["type_column"]
            ):
                column["column"] = CompositeType()
        else:
            request["flash_messages"].append(
                (
                    f"Errors: Not exists table defined in Header of Composite CSV File. "
                    f"Column names in Composite CSV must be like 'table_name:column_name'. "
                    f"You set: {column_name}. Table {table_name} does not exist",
                    "error",
                )
            )
            return request, None, None
        if tables_indexes[table_name]["start"] is None:
            tables_indexes[table_name]["start"] = num
            tables_indexes[table_name]["end"] = num
        else:
            tables_indexes[table_name]["end"] = num

        if not column["column"]:
            # if we don't set it as CompositeType()
            column["column"] = _column_name
        header_columns.append(column)

    return None, header_columns, tables_indexes


async def create_or_update(row, model_id):
    print(row)
    try:
        await cfg.models[model_id]["model"].create(**row)
    except asyncpg.exceptions.UniqueViolationError as e:
        if cfg.csv_update_existed:
            model_data = cfg.models[model_id]
            obj_id = row[model_data["key"]]
            obj = await model_data["model"].get(
                model_data["columns_data"][model_data["key"]]["type"](obj_id)
            )
            await obj.update(**row).apply()
            return None, row[model_data["key"]], None
        else:
            return None, None, (row[cfg.models[model_id]["key"]], e.args)
    except Exception as e:
        return None, None, (row[cfg.models[model_id]["key"]], e.args)
    return row[cfg.models[model_id]["key"]], None, None


async def upload_simple_csv_row(row, header, model_id):
    columns_data = cfg.models[model_id]["columns_data"]
    row = {header[index]: value for index, value in enumerate(row)}
    row = reverse_hash_names(model_id, row)
    row = correct_types(row, columns_data)
    return await create_or_update(row, model_id)


async def upload_composite_csv_row(row, header, tables_indexes, stack, unique_keys):
    # if composite header each column == {'table': {}, 'column': None}
    # todo: refactor this huge code
    table_num = 0
    previous_table_name = None
    for table_name, indexes in tables_indexes.items():
        # {'start': None, 'end': None}

        table_header = deepcopy(header)[
            indexes["start"] : indexes["end"] + 1  # noqa E203
        ]
        table_row_data = deepcopy(row)[
            indexes["start"] : indexes["end"] + 1  # noqa E203
        ]
        if not any(table_row_data):
            if table_header[0]["table"][0] == table_header[0]["table"][1]:
                previous_table_name = table_name
            else:
                for elem in stack[::-1]:
                    if elem in table_header[0]["table"][1]:
                        previous_table_name = elem
                        break
            table_num += 1
            continue
        if table_header[0]["table"][0] == table_header[0]["table"][1]:
            model_id = table_name
            columns_data = cfg.models[model_id]["columns_data"]
        else:
            model_id = None
            columns_indexes_remove = []
            for index, field_value in enumerate(table_header):
                if isinstance(field_value["column"], CompositeType):
                    model_id = table_row_data[index]
                    table_row_data.pop(index)
                    break
            if model_id:
                table_header.pop(index)
            else:
                model_id = cfg.composite_csv_settings[table_name]["pattern"].replace(
                    "*", previous_table_name
                )

            columns_data = cfg.models[model_id]["columns_data"]

            for index, value in enumerate(table_header):
                if value["column"] not in columns_data:
                    # column not in this table
                    columns_indexes_remove.append(index)
            for num, index in enumerate(columns_indexes_remove):
                table_header.pop(index - num)
                table_row_data.pop(index - num)

        table_row = {
            table_header[num]["column"]: value
            for num, value in enumerate(table_row_data)
        }
        try:
            table_row = reverse_hash_names(model_id, table_row)
            table_row = correct_types(table_row, columns_data)
            if table_num > 0:
                column, target_column = cfg.models[model_id]["foreign_keys"][
                    previous_table_name
                ]

                foreing_column_value = unique_keys[previous_table_name][target_column]
                table_row[column] = foreing_column_value
            id_added, id_updated, error = await create_or_update(table_row, model_id)
            if id_added or id_updated:
                model_data = cfg.models[model_id]
                new_obj = await model_data["model"].get(
                    model_data["columns_data"][model_data["key"]]["type"](
                        id_added or id_updated
                    )
                )
                if indexes["start"] == 0:
                    unique_keys = {}
                unique_keys[model_id] = new_obj
                stack.append(model_id)
                previous_table_name = model_id
                table_num += 1
            else:
                return None, id_updated, error, stack, unique_keys
        except Exception as e:
            raise e
            return None, None, (table_row, e), stack, unique_keys
            # TODO: right now just abort if error during composite file upload
        return id_added, id_updated, None, stack, unique_keys


async def insert_data_from_csv(file_path: Text, model_id: Text, request: Request):
    """ file_path - path to csv file"""
    with open(file_path, "r") as read_obj:
        # pass the file object to reader() to get the reader object
        csv_reader = reader(read_obj)
        # Iterate over each row in the csv using reader object
        header = None
        ids_added = []
        ids_updated = []
        try:
            errors = []
            unique_keys = {}
            stack = []
            for num, row in enumerate(csv_reader):
                # row variable is a list that represents a row in csv
                if num == 0:
                    error_request, header, composite = process_csv_header(
                        model_id, row, request
                    )
                    if error_request:
                        return error_request, False
                    if composite:
                        (
                            error_request,
                            header,
                            tables_indexes,
                        ) = extract_tables_from_header(header, request)
                        if error_request:
                            return error_request, False
                    continue
                if not composite:
                    id_added, id_updated, error = await upload_simple_csv_row(
                        row, header, model_id
                    )
                    if id_updated:
                        ids_updated.append(id_updated)
                    elif error:
                        errors.append(error)
                        continue
                    elif id_added:
                        ids_added.append(id_added)
                else:
                    (
                        id_added,
                        id_updated,
                        error,
                        stack,
                        unique_keys,
                    ) = await upload_composite_csv_row(
                        row, header, tables_indexes, stack, unique_keys
                    )
                    if errors:
                        errors.append(error)
                        return request, False
                    if id_added:
                        ids_added.append(id_added)
                    if id_updated:
                        ids_updated.append(id_updated)
            if errors:
                request["flash_messages"].append(
                    (
                        f"Errors: was not added  (row number, row {cfg.models[model_id]['key']}, error) : {errors}",
                        "error",
                    )
                )

            base_msg = (
                "Objects"
                if composite
                else f"Objects with {cfg.models[model_id]['key']}:"
            )
            if ids_added:
                request["flash_messages"].append(
                    (f"{base_msg}{ids_added} was added", "success")
                )
            if ids_updated:
                request["flash_messages"].append(
                    (f" {base_msg}{ids_updated} was updated", "success")
                )
        except ValueError as e:
            raise e
            request["flash_messages"].append((e.args, "error"))
        except asyncpg.exceptions.ForeignKeyViolationError as e:
            request["flash_messages"].append((e.args, "error"))
        except asyncpg.exceptions.NotNullViolationError as e:
            column = e.args[0].split("column")[1].split("violates")[0]
            request["flash_messages"].append(
                (f"Field {column} cannot be null", "error")
            )
        return request, True


async def drop_and_recreate_all_tables():
    for model_id in cfg.models:
        sql_query = f"DROP TABLE {model_id} CASCADE"
        try:
            await cfg.app.db.status(cfg.app.db.text(sql_query))
        except asyncpg.exceptions.UndefinedTableError:
            # if table not exist just ignore it
            pass
    await cfg.app.db.gino.create_all()


async def render_add_or_edit_form(
    request: Request, model_id: Text, obj_id: Text = None
) -> HTTPResponse:

    model_data = cfg.models[model_id]
    model = cfg.models[model_id]["model"]
    if obj_id:
        obj_id = model_data["columns_data"][model_data["key"]]["type"](obj_id)
        obj = serialize_dict((await model.get(obj_id)).to_dict())
        add = False
    else:
        obj = {}
        add = True
    return cfg.jinja.render(
        "add_form.html",
        request,
        model=model_id,
        add=add,
        obj=obj,
        columns={
            column_name: {"len": model_data["columns_data"][column_name]["len"]}
            for column_name in model_data["columns_names"]
        },
    )


async def count_elements_in_db():
    data = {}
    for model_id, value in cfg.models.items():
        try:
            data[model_id] = await cfg.app.db.func.count(
                getattr(value["model"], value["key"])
            ).gino.scalar()
        except asyncpg.exceptions.UndefinedTableError:
            data[model_id] = "Table does not exist"
    return data


async def create_object_copy(
    model_id: Text,
    base_object_key: Text,
    fk_column: Column = None,
    new_fk_link_id: Text = None,
) -> str:
    model_data = cfg.models[model_id]
    columns_data = model_data["columns_data"]
    key = model_data["key"]
    base_object_key = columns_data[key]["type"](base_object_key)
    model = cfg.models[model_id]["model"]
    # id can be str or int
    # todo: need fix for several unique columns
    if isinstance(base_object_key, str):
        new_obj_key = (
            base_object_key
            + f"{'_' if not base_object_key.endswith('_') else ''}"
            + uuid.uuid1().hex[5:10]
        )
        len_ = model_data["columns_data"][key]["len"]
        if len_:
            if new_obj_key[:len_] == base_object_key:
                # if we spend all id previous
                new_obj_key = new_obj_key[
                    len_ : len_ + len_  # noqa E203
                ]  # auto format from black
            else:
                new_obj_key = new_obj_key[:len_]
    else:
        # todo: need to check ints with max size
        new_obj_key = base_object_key + randint(0, 10000000000)

    bas_obj = (await model.get(base_object_key)).to_dict()

    bas_obj[key] = new_obj_key

    if new_fk_link_id and fk_column is not None:
        bas_obj[fk_column.name] = new_fk_link_id

    for item in model_data["required_columns"]:
        # todo: need to document this behaviour in copy step
        if (item in bas_obj and not bas_obj[item]) or item not in bas_obj:
            bas_obj[item] = bas_obj[key]
            if columns_data[item]["type"] == "HASH":
                bas_obj[item] = cfg.hash_method(bas_obj[key])
    new_obj = reverse_hash_names(model_id, bas_obj)
    await model.create(**new_obj)
    return new_obj_key


async def deepcopy_recursive(
    model: Model,
    object_id: str,
    new_fk_link_id: Optional[str] = None,
    fk_column: Optional[Column] = None,
):
    logger.debug(
        f"Making a deepcopy of {model} with id {object_id} linking to foreign key"
        f" {fk_column} with id {new_fk_link_id}"
    )
    new_obj_key = await create_object_copy(
        model.__tablename__, object_id, fk_column, new_fk_link_id
    )
    primary_key_col = identity(model)[0]
    dependent_models = {}
    # TODO(ehborisov): check how it works in the case of composite key
    for m_id, data in cfg.models.items():
        for column in cfg.app.db.tables[m_id].columns:
            if column.references(primary_key_col):
                dependent_models[data["model"]] = column
    for dep_model in dependent_models:
        fk_column = dependent_models[dep_model]
        all_referencing_instance_ids = (
            await dep_model.select(identity(dep_model)[0].name)
            .where(fk_column == object_id)
            .gino.all()
        )
        # TODO(ehborisov): can gather be used there? Only if we have a connection pool?
        for inst_id in all_referencing_instance_ids:
            await deepcopy_recursive(dep_model, inst_id[0], new_obj_key, fk_column)
    logger.debug(f"Finished copying, returning newly created object's id {new_obj_key}")
    return new_obj_key
