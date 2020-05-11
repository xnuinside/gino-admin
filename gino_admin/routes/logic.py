import uuid
from copy import deepcopy
from csv import reader
from random import randint
from typing import Dict, List, Text

import asyncpg
from gino.declarative import Model
from sanic.log import logger
from sanic.request import Request
from sanic.response import HTTPResponse

from gino_admin.core import cfg, jinja
from gino_admin.utils import (correct_types, extract_columns_data,
                              reverse_hash_names)


async def render_model_view(request: Request, model_id: Text) -> HTTPResponse:
    """ render model data view """
    columns_data, hashed_indexes = extract_columns_data(model_id)
    columns_names = list(columns_data.keys())
    model = cfg.app.db.tables[model_id]
    query = cfg.app.db.select([model])
    rows = await query.gino.all()
    output = []
    for row in rows:
        row = {columns_names[num]: field for num, field in enumerate(row)}
        for index in hashed_indexes:
            row[columns_names[index]] = "*************"
        output.append(row)
    output = output[::-1]
    _response = jinja.render(
        "model_view.html",
        request,
        model=model_id,
        columns=columns_names,
        model_data=output,
        objects=cfg.models,
        url_prefix=cfg.URL_PREFIX,
    )
    return _response


async def insert_data_from_csv(file_path: Text, model_id: Text, request: Request):
    """ file_path - path to csv file"""
    with open(file_path, "r") as read_obj:
        # pass the file object to reader() to get the reader object
        csv_reader = reader(read_obj)
        # Iterate over each row in the csv using reader object
        header = None
        id_added = []
        try:
            errors = []
            for num, row in enumerate(csv_reader):
                # row variable is a list that represents a row in csv
                if num == 0:
                    columns_data, hashed_indexes = extract_columns_data(model_id)
                    columns_names = list(columns_data.keys())
                    header = [x.strip().replace("\ufeff", "") for x in row]
                    hashed_columns_names = [
                        columns_names[index] for index in hashed_indexes
                    ]
                    validate_header = deepcopy(header)
                    for _num, name in enumerate(validate_header):
                        if name in hashed_columns_names:
                            validate_header[_num] = name + "_hash"
                        if name not in columns_names:
                            request["flash"](
                                f"Wrong columns in CSV file. Header did not much model's columns. "
                                f"For {model_id.capitalize()} possible columns {columns_names}",
                                "error",
                            )
                            return request, False
                else:
                    row = {header[index]: value for index, value in enumerate(row)}
                    row = reverse_hash_names(hashed_indexes, columns_names, row)
                    row = correct_types(row, columns_data)
                    try:
                        await cfg.models[model_id].create(**row)
                    except Exception as e:
                        errors.append((num, row["id"], e.args))
                        continue
                    id_added.append(row["id"])
            if errors:
                request["flash"](
                    f"Errors: was not added  (row number, row id, error) : {errors}",
                    "error",
                )
            request["flash"](f"Objects with ids {id_added} was added", "success")
        except ValueError as e:
            request["flash"](e.args, "error")
        except asyncpg.exceptions.ForeignKeyViolationError as e:
            request["flash"](e.args, "error")
        except asyncpg.exceptions.UniqueViolationError:
            request["flash"](
                f"{model_id.capitalize()} with id '{row['id']}' already exists", "error"
            )
        except asyncpg.exceptions.NotNullViolationError as e:
            column = e.args[0].split("column")[1].split("violates")[0]
            request["flash"](f"Field {column} cannot be null", "error")
    return request, True


async def drop_and_recreate_all_tables():
    for model_id in cfg.models:
        sql_query = f"DROP TABLE {model_id} CASCADE"
        await cfg.app.db.status(cfg.app.db.text(sql_query))
    await cfg.app.db.gino.create_all()


async def create_object_copy(
    base_obj: Dict, model: Model, columns_data: Dict, hashed_indexes: List[int]
) -> str:
    logger.debug(f"creating object copy of {base_obj} of model {model}")
    object_id = base_obj["id"]
    # id can be str or int
    if isinstance(object_id, str):
        new_obj_id = object_id + "_copy_" + uuid.uuid1().hex[5:10]
    else:
        new_obj_id = object_id + randint(0, 10000000000)
    base_obj["id"] = new_obj_id
    required = [
        key for key, value in columns_data.items() if value["nullable"] is False
    ]
    for item in required:
        # todo: need to document this behaviour in copy step
        if (item in base_obj and not base_obj[item]) or item not in base_obj:
            base_obj[item] = base_obj["id"]
            if columns_data[item]["type"] == "HASH":
                base_obj[item] = cfg.hash_method(base_obj["id"])
    columns_names = list(columns_data.keys())
    bas_obj = reverse_hash_names(hashed_indexes, columns_names, base_obj)
    await model.create(**bas_obj)
    return new_obj_id
