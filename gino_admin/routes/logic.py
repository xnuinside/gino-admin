from collections import defaultdict
from copy import deepcopy
from csv import reader
from typing import List, Text

import asyncpg
from sanic.request import Request
from sanic.response import HTTPResponse

from gino_admin.core import cfg, jinja
from gino_admin.utils import (CompositeType, correct_types, reverse_hash_names,
                              serialize_dict)


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
    _response = jinja.render(
        "model_view.html",
        request,
        model=model_id,
        columns=columns_names,
        model_data=output,
        unique=cfg.models[model_id]["key"],
        objects=cfg.models,
        url_prefix=cfg.URL_PREFIX,
    )
    return _response


def process_csv_header(model_id, row, request):
    composite = False
    columns_names = cfg.models[model_id]["columns_names"]
    hashed_indexes = cfg.models[model_id]["hashed_indexes"]

    header = [x.strip().replace("\ufeff", "") for x in row]
    hashed_columns_names = [columns_names[index] for index in hashed_indexes]
    if ":" in header[0]:
        composite = True
    if not composite:
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

            if _column_name == cfg.composite_csv_settings[table_name]["type_column"]:
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


async def insert_data_from_csv(file_path: Text, model_id: Text, request: Request):
    """ file_path - path to csv file"""
    columns_data = cfg.models[model_id]["columns_data"]
    with open(file_path, "r") as read_obj:
        # pass the file object to reader() to get the reader object
        csv_reader = reader(read_obj)
        # Iterate over each row in the csv using reader object
        header = None
        id_added = []
        try:
            errors = []
            unique_keys = {}
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
                    row = {header[index]: value for index, value in enumerate(row)}
                    row = reverse_hash_names(model_id, row)
                    row = correct_types(row, columns_data)
                    try:
                        await cfg.models[model_id]["model"].create(**row)
                    except Exception as e:
                        errors.append((num, row[cfg.models[model_id]["key"]], e.args))
                        continue
                    id_added.append(row[cfg.models[model_id]["key"]])
                else:
                    # if composite header each column == {'table': {}, 'column': None}
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
                            previous_table_name = table_name
                            table_num += 1
                            print("ANY")
                            continue
                        print(unique_keys)
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
                            table_header.pop(index)

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
                                column, target_column = cfg.models[model_id][
                                    "foreign_keys"
                                ][previous_table_name]

                                foreing_column_value = unique_keys[previous_table_name][
                                    target_column
                                ]
                                table_row[column] = foreing_column_value
                            new_obj = (
                                await cfg.models[model_id]["model"].create(**table_row)
                            ).to_dict()
                            # todo: add support to multi unique values
                            unique_keys[model_id] = new_obj
                            previous_table_name = table_name
                            table_num += 1
                        except Exception as e:
                            raise e
                            errors.append((num, table_row, e))
                            # TODO: right now just abort if error during composite file upload
                            return request, False

                        id_added.append(new_obj[cfg.models[model_id]["key"]])

            if errors:
                request["flash_messages"].append(
                    (
                        f"Errors: was not added  (row number, row {cfg.models[model_id]['key']}, error) : {errors}",
                        "error",
                    )
                )
            request["flash_messages"].append(
                (
                    f"Objects with {cfg.models[model_id]['key']} {id_added} was added",
                    "success",
                )
            )
        except ValueError as e:

            raise e
            request["flash_messages"].append((e.args, "error"))
        except asyncpg.exceptions.ForeignKeyViolationError as e:
            request["flash_messages"].append((e.args, "error"))
        except asyncpg.exceptions.UniqueViolationError:
            request["flash_messages"].append(
                (
                    f"{model_id.capitalize()} with id '{table_row[cfg.models[model_id]['key']]}' already exists",
                    "error",
                )
            )
        except asyncpg.exceptions.NotNullViolationError as e:
            column = e.args[0].split("column")[1].split("violates")[0]
            request["flash_messages"].append(
                (f"Field {column} cannot be null", "error")
            )
        return request, True


async def drop_and_recreate_all_tables():
    for model_id in cfg.models:
        sql_query = f"DROP TABLE {model_id} CASCADE"
        await cfg.app.db.status(cfg.app.db.text(sql_query))
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
    return jinja.render(
        "add_form.html",
        request,
        model=model_id,
        add=add,
        obj=obj,
        objects=cfg.models,
        columns={
            column_name: {"len": model_data["columns_data"][column_name]["len"]}
            for column_name in model_data["columns_names"]
        },
        url_prefix=cfg.URL_PREFIX,
    )


async def count_elements_in_db():
    data = {}
    for model_id, value in cfg.models.items():
        data[model_id] = await cfg.app.db.func.count(
            getattr(value["model"], value["key"])
        ).gino.scalar()
    return data
