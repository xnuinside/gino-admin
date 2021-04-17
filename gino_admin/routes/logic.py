from collections import defaultdict
from copy import deepcopy
from csv import reader
from io import BytesIO, TextIOWrapper
from typing import Any, Dict, List, Optional, Text, Tuple

import asyncpg
from gino.declarative import Model
from sanic.log import logger
from sanic.request import File, Request
from sanic.response import HTTPResponse
from sqlalchemy.sql.schema import Column
from sqlalchemy_utils.functions import identity

from gino_admin import config
from gino_admin.history import log_history_event
from gino_admin.utils import (CompositeType, correct_types,
                              create_obj_id_for_query, generate_new_id,
                              get_obj_id_from_row, get_table_name,
                              get_type_name, prepare_request_params,
                              reverse_hash_names, serialize_dict)

cfg = config.cfg


def columns_data_for_ui(columns_data: Dict, model_data: Dict) -> Dict:
    return {
        column_name: {
            "len": columns_data[column_name]["len"],
            "type": get_type_name(columns_data[column_name]),
            "disabled": columns_data[column_name]["sequence"],
        }
        for column_name in model_data["columns_names"]
    }


async def render_model_view(request: Request, model_id: Text) -> HTTPResponse:
    """ render model data view """
    model_data = cfg.models[model_id]
    columns_names = model_data["columns_names"]
    table_name = get_table_name(model_id)
    model = cfg.app.db.tables[table_name]
    query = cfg.app.db.select([model])
    columns_data = model_data["columns_data"]
    try:
        rows = await query.gino.all()
    except asyncpg.exceptions.UndefinedTableError:
        await cfg.app.db.gino.create_all(tables=[model])
        rows = await query.gino.all()
    output = []
    for row in rows:
        row = {columns_names[num]: field for num, field in enumerate(row)}
        row["_id"] = create_obj_id_for_query(get_obj_id_from_row(model_data, row))
        for index in cfg.models[model_id]["hashed_indexes"]:
            row[columns_names[index]] = "*************"
        output.append(row)
    output = output[::-1]

    _response = cfg.jinja.render(
        "model_view.html",
        request,
        model=model_id,
        columns=columns_data_for_ui(columns_data, model_data),
        model_data=output,
        unique=cfg.models[model_id]["identity"],
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
                request.ctx.flash_messages.append(
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
            request.ctx.flash_messages.append(
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
            request.ctx.flash_messages.append(
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


async def create_or_update(row: Dict, model_id: Text) -> Tuple:
    try:
        model_data = cfg.models[model_id]
        row = prepare_request_params(row, model_id, model_data)
        obj = (await model_data["model"].create(**row)).to_dict()
        obj_id = get_obj_id_from_row(model_data, obj)
        return obj_id, None, None
    except asyncpg.exceptions.UniqueViolationError as e:
        if cfg.csv_update_existed:
            obj_id = prepare_request_params(
                get_obj_id_from_row(model_data, row), model_id, model_data
            )
            obj = await get_by_params(obj_id, model_data["model"])
            await obj.update(**row).apply()
            return None, obj_id, None
        else:
            return None, None, (row, e.args)
    except Exception as e:
        return None, None, (row, e.args)


async def upload_simple_csv_row(row, header, model_id):
    row = {header[index]: value for index, value in enumerate(row)}
    row = prepare_request_params(row, model_id, cfg.models[model_id])
    return await create_or_update(row, model_id)


async def upload_composite_csv_row(row, header, tables_indexes, stack, unique_keys):
    # if composite header each column == {'table': {}, 'column': None}
    # todo: refactor this huge code
    table_num = 0
    previous_table_name = None
    id_added = []
    id_updated = []
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
        model_data = cfg.models[model_id]
        try:
            table_row = prepare_request_params(table_row, model_id, model_data)
            if table_num > 0:
                column, target_column = cfg.models[model_id]["foreign_keys"][
                    previous_table_name
                ]
                foreing_column_value = unique_keys[previous_table_name][target_column]
                table_row[column] = foreing_column_value
            id_added, id_updated, error = await create_or_update(table_row, model_id)
            if id_added or id_updated:
                id_ = id_added if id_added else id_updated
                new_obj = (await get_by_params(id_, model_data["model"])).to_dict()

                if indexes["start"] == 0:
                    unique_keys = {}
                unique_keys[model_id] = new_obj
                stack.append(model_id)
                previous_table_name = model_id
                table_num += 1
            else:
                return None, id_updated, error, stack, unique_keys
        except Exception as e:
            return None, None, (table_row, e), stack, unique_keys
            # TODO: right now just abort if error during composite file upload
    return id_added, id_updated, None, stack, unique_keys


async def insert_data_from_csv_file(file_path: Text, model_id: Text, request: Request):
    """ file_path - path to csv file in the filesystem"""
    with open(file_path, "r") as read_obj:
        return await insert_data_from_csv_rows(read_obj, model_id, request)


async def upload_from_csv_data(
    upload_file: File, file_name: Text, request: Request, model_id: Text
):
    with TextIOWrapper(BytesIO(upload_file.body)) as read_obj:
        request, is_success = await insert_data_from_csv_rows(
            read_obj, model_id, request
        )
        if is_success:
            log_history_event(
                request,
                f"Upload data from CSV from file {file_name} to model {model_id}",
                "system: upload_csv",
            )
        return request, is_success


async def insert_data_from_csv_rows(read_obj: Any, model_id: Text, request: Request):
    """ process the data from the in-memory csv file object """
    # Iterate over each row in the csv using reader object
    csv_reader = reader(read_obj)
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
            request.ctx.flash_messages.append(
                (
                    f"Errors: {errors}",
                    "error",
                )
            )

        base_msg = "Objects" if composite else "Objects"
        if ids_added:
            request.ctx.flash_messages.append(
                (f"{base_msg}{ids_added} was added", "success")
            )
        if ids_updated:
            request.ctx.flash_messages.append(
                (f"{base_msg}{ids_updated} was updated", "success")
            )
    except ValueError as e:
        request.ctx.flash_messages.append((e.args, "error"))
        raise e
    except asyncpg.exceptions.ForeignKeyViolationError as e:
        request.ctx.flash_messages.append((e.args, "error"))
    except asyncpg.exceptions.NotNullViolationError as e:
        column = e.args[0].split("column")[1].split("violates")[0]
        request.ctx.flash_messages.append((f"Field {column} cannot be null", "error"))
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


async def update_all_by_params(update_params: Dict, where_params: Dict, model):
    q = model.update.values(**update_params)
    operand_types = {"==": "__eq__", "in": "contains"}
    for attr, value in where_params.items():
        field = getattr(model, attr)
        if isinstance(value, list):
            in_query = ":|"
            if in_query in value[0]:
                final_ = []
                operand_name = operand_types["in"]
                value = value[0].split(in_query)[0]
                final_.append(value)
                value = final_
            else:
                operand_name = operand_types["=="]
        else:
            operand_name = operand_types["=="]
        operand = getattr(field, operand_name)
        if value != "":
            q = q.where(operand(value))
    items = await q.gino.status()
    return items


async def delete_all_by_params(query_params: Dict, model):
    q = model.delete
    operand_types = {"==": "__eq__", "in": "contains"}
    for attr, value in query_params.items():
        field = getattr(model, attr)
        if isinstance(value, list):
            in_query = ":|"
            if in_query in value[0]:
                final_ = []
                operand_name = operand_types["in"]
                value = value[0].split(in_query)[0]
                final_.append(value)
                value = final_
            else:
                operand_name = operand_types["=="]
        else:
            operand_name = operand_types["=="]
        operand = getattr(field, operand_name)
        if value != "":
            q = q.where(operand(value))
    items = await q.gino.status()
    return items


async def get_by_params(query_params: Dict, model):
    q = model.query
    operand_types = {"==": "__eq__", "in": "contains"}
    for attr, value in query_params.items():
        field = getattr(model, attr)
        if isinstance(value, list):
            in_query = ":|"
            if in_query in value[0]:
                final_ = []
                operand_name = operand_types["in"]
                value = value[0].split(in_query)[0]
                final_.append(value)
                value = final_
            else:
                operand_name = operand_types["=="]
        else:
            operand_name = operand_types["=="]
        operand = getattr(field, operand_name)
        if value != "":
            q = q.where(operand(value))
    items = await q.gino.first()
    return items


async def render_add_or_edit_form(
    request: Request, model_id: Text, obj_id: Dict = None
) -> HTTPResponse:
    model_data = cfg.models[model_id]
    model = cfg.models[model_id]["model"]
    columns_data = model_data["columns_data"]
    if obj_id:
        obj_id = correct_types(obj_id, columns_data, no_default=True)
        obj = await get_by_params(obj_id, model)
        if obj:
            obj = serialize_dict(obj.to_dict())
        else:
            request.ctx.flash_messages.append(
                (f"obj with id {obj_id} was not found", "error")
            )
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
        columns=columns_data_for_ui(columns_data, model_data),
    )


async def count_elements_in_db():
    data = {}
    for model_id, value in cfg.models.items():
        try:
            table_name = get_table_name(model_id)
            sql_query = f"SELECT COUNT(*) FROM {table_name}"
            data[model_id] = (await cfg.app.db.status(cfg.app.db.text(sql_query)))[1][
                0
            ][0]
        except asyncpg.exceptions.UndefinedTableError:
            data[model_id] = "Table does not exist"
    return data


async def create_object_copy(
    model_id: Text,
    base_obj_id: Text,
    model_data: Dict,
    *,
    fk_column: Column = None,
    new_fk_link_id: Text = None,
    new_id: Optional[Text] = None,
) -> str:
    model_data = cfg.models[model_id]
    columns_data = model_data["columns_data"]
    model = cfg.models[model_id]["model"]
    if not new_id:
        new_obj_key = generate_new_id(base_obj_id, columns_data)
    else:
        for key in new_id:
            _len = columns_data[key]["len"]
            if _len:
                new_id[key] = new_id[key][:_len]
        new_obj_key = new_id
    base_obj_id = correct_types(base_obj_id, columns_data, no_default=True)
    bas_obj = await get_by_params(base_obj_id, model)
    bas_obj = bas_obj.to_dict()
    bas_obj.update(new_obj_key)
    if new_fk_link_id and fk_column is not None:
        bas_obj[fk_column.name] = new_fk_link_id
    new_obj = correct_types(reverse_hash_names(model_id, bas_obj), columns_data)
    await model.create(**new_obj)
    return new_obj_key


async def deepcopy_recursive(
    model: Model,
    object_id: str,
    model_data: Dict,
    *,
    new_fk_link_id: Optional[str] = None,
    fk_column: Optional[Column] = None,
    new_id: Optional[str] = None,
):
    logger.debug(
        f"Making a deepcopy of {model} with id {object_id} linking to foreign key"
        f" {fk_column} with id {new_fk_link_id}"
    )
    new_obj_key = await create_object_copy(
        model.__tablename__,
        object_id,
        model_data,
        fk_column=fk_column,
        new_fk_link_id=new_fk_link_id,
        new_id=new_id,
    )
    if len(identity(model)) == 0:
        primary_key_col = object_id
        return (
            "Deepcopy does not available for tables without primary keys right now",
            "error",
        )
    else:
        primary_key_col = identity(model)[0]

    dependent_models = {}
    # TODO(ehborisov): check how it works in the case of composite key
    for m_id, data in cfg.models.items():
        table_name = get_table_name(m_id)
        for column in cfg.app.db.tables[table_name].columns:
            if column.references(primary_key_col):
                dependent_models[data["model"]] = column
    for dep_model in dependent_models:
        fk_column = dependent_models[dep_model]
        all_referencing_instance_ids = (
            await dep_model.select(identity(dep_model)[0].name)
            .where(fk_column == object_id[primary_key_col.name])
            .gino.all()
        )
        # TODO(ehborisov): can gather be used there? Only if we have a connection pool?
        for inst_id in all_referencing_instance_ids:
            result = await deepcopy_recursive(
                dep_model,
                {identity(dep_model)[0].name: inst_id[0]},
                model_data,
                new_fk_link_id=new_obj_key[identity(model)[0].name],
                fk_column=fk_column,
            )
            if isinstance(result, tuple):
                return result
    logger.debug(f"Finished copying, returning newly created object's id {new_obj_key}")
    return new_obj_key
