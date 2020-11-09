import datetime
import logging
import os
import re
import time
import uuid
from ast import literal_eval
from random import randint
from typing import Any, Dict, List, Text, Union
from unicodedata import normalize

import aiofiles
import dsnparse
import yaml
from passlib.hash import pbkdf2_sha256
from sqlalchemy.types import BigInteger

from gino_admin import config

cfg = config.cfg
logger = logging.getLogger("Gino Admin")

salt = uuid.uuid4().hex


class HashColumn:
    pass


_windows_device_files = (
    "CON",
    "AUX",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "LPT1",
    "LPT2",
    "LPT3",
    "PRN",
    "NUL",
)


class GinoAdminError(Exception):
    pass


class CompositeType:
    pass


def serialize_obj(obj: Any) -> Any:
    """ method to serialise datetime obj """
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    else:
        return obj


def serialize_dict(container: Dict) -> Dict:
    """ method to serialise datetime in dict """
    for key, value in container.items():
        container[key] = serialize_obj(value)
    return container


def reverse_hash_names(model_id: Text, request_params: Dict):
    model_data = cfg.models[model_id]
    for hashed_index in model_data["hashed_indexes"]:
        if model_data["columns_names"][hashed_index] in request_params:
            request_params[
                model_data["columns_names"][hashed_index] + "_hash"
            ] = cfg.hash_method(
                request_params[model_data["columns_names"][hashed_index]]
            )
            del request_params[model_data["columns_names"][hashed_index]]
    return request_params


def secure_filename(filename: Text):
    filename = normalize("NFKD", filename).encode("ascii", "ignore")
    filename = filename.decode("ascii")
    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, " ")
    _filename_ascii_strip_re = re.compile(r"[^A-Za-z0-9_.-]")
    filename = str(_filename_ascii_strip_re.sub("", "_".join(filename.split()))).strip(
        "._"
    )
    if (
        os.name == "nt"
        and filename
        and filename.split(".")[0].upper() in _windows_device_files
    ):
        filename = "_" + filename

    return filename


def valid_file_type(file_name: Text, file_type: Text, allowed_file_types: List):
    file_name_type = file_name.split(".")[-1]
    for allowed_type in allowed_file_types:
        if file_name_type == allowed_type and (
            file_type == f"application/{allowed_type}"
            or file_type == f"text/{allowed_type}"
        ):
            return True
    else:
        return False


def valid_file_size(file_body: bytes, max_size: int):
    if len(file_body) < max_size:
        return True
    return False


async def write_file(path, body):
    async with aiofiles.open(path, "wb") as f:
        await f.write(body)
        f.close()


def correct_types(params: Dict, columns_data: Dict, no_default=False):
    to_del = []
    for param in params:
        if "_hash" in param:
            param_type = columns_data[param.replace("_hash", "")]["type"]
        else:
            param_type = columns_data[param]["type"]

        if not params[param]:
            # mean None
            to_del.append(param)
            continue
        if isinstance(param, CompositeType):
            continue
        if not isinstance(param_type, tuple):
            if "_hash" not in param and not isinstance(params[param], param_type):
                if param_type == list:
                    params[param] = params[param].split(",")
                elif param_type in [datetime.datetime, datetime.date, datetime.time]:
                    params[param] = extract_datetime(params[param], param_type)
                elif param_type == HashColumn:
                    continue
                else:
                    params[param] = param_type(params[param])

        else:
            if param_type[0] == list:
                if "[" in params[param] and isinstance(params[param], str):
                    params[param] = literal_eval(params[param])
                else:
                    real_param = []
                    real_param.append(params[param])
                    params[param] = real_param
                elements_type = param_type[1]
                formatted_list = []
                for elem in params[param]:
                    formatted_list.append(elements_type(elem))
                params[param] = formatted_list
    for param in to_del:
        del params[param]
    if not no_default:
        for column in columns_data:
            if columns_data[column]["type"] == bool and column not in params:
                params[column] = False
    return params


def parse_datetime(datetime_str: Text) -> datetime.datetime:
    """ form string parse datetime """
    for str_format in cfg.datetime_str_formats:
        try:
            datetime_object = datetime.datetime.strptime(datetime_str, str_format)
            return datetime_object
        except ValueError:
            continue


def parse_date(date_str: Text) -> datetime.date:
    for str_format in cfg.date_str_formats:
        try:
            date_object = datetime.datetime.strptime(date_str, str_format).date()
            return date_object
        except ValueError:
            continue


def parse_time(date_str: Text) -> datetime.time:
    for str_format in cfg.time_str_formats:
        try:
            date_object = datetime.datetime.strptime(date_str, str_format).time()
            return date_object
        except ValueError:
            continue


def extract_datetime(
    datetime_str: Text, type_: Union[datetime.datetime, datetime.date]
):
    """ parse datetime or date object from string """
    if type_ == datetime.datetime:
        return parse_datetime(datetime_str)
    elif type_ == datetime.date:
        return parse_date(datetime_str)
    elif type_ == datetime.time:
        return parse_time(datetime_str)


def prepare_request_params(
    request_params: Dict, model_id: Text, model_data: Dict
) -> Dict:
    """ reverse hash names and correct types of input params """
    request_params = correct_types(request_params, model_data["columns_data"])
    if model_data["hashed_indexes"]:
        request_params = reverse_hash_names(model_id, request_params)
    return request_params


def get_type_name(column_data: Dict) -> Text:
    """ get type name for ui """
    column_type = str(column_data["db_type"]).lower()
    if "text" in column_type:
        return "text"
    elif "json" in column_type:
        return "json"
    elif not isinstance(column_data["type"], tuple):
        type_ = column_data["type"].__name__
    else:
        type_ = f'array of {column_data["type"][1]}'
    return type_


def generate_token(ip: Text):
    """ generate session token based on user name and salt """
    return pbkdf2_sha256.encrypt(salt + ip)


def read_yaml(preset_file: Text) -> Dict:
    """ read preset yaml file"""
    with open(preset_file, "r") as preset_file:
        return yaml.safe_load(preset_file)


def get_presets():
    """ return previous loaded, or re-read from disk """
    if not cfg.presets or (
        cfg.presets.get("loaded_at")
        and cfg.presets["loaded_at"] < os.path.getmtime(cfg.presets_folder)
    ):
        cfg.presets = {"presets": load_presets(), "loaded_at": time.time()}
    return cfg.presets


def get_preset_by_id(preset_id: Text):
    """ get preset by id """
    presets = get_presets()["presets"]
    for preset in presets:
        if preset_id == preset["id"]:
            return preset


def load_presets():
    """ get presets data from yml configs from presets folder"""
    presets = []
    if not os.path.isdir(cfg.presets_folder):
        if os.path.isfile(cfg.presets_folder):
            logger.error(f"Presets folder is file. Must be a path to folder")
        logger.info(f"Presets folder not found. Create new folder.")
        os.makedirs(cfg.presets_folder)
    else:
        for file_name in os.listdir(cfg.presets_folder):
            if file_name.endswith(".yml"):
                file_path = os.path.join(cfg.presets_folder, file_name)
                preset_definition = read_yaml(file_path)
                presets.append(preset_definition)
    return presets


def get_settings():
    """ gino admin settings '"""
    settings = {}
    for setting in cfg.displayable_setting:
        settings[setting] = getattr(cfg, setting)
    return settings


def get_obj_id_from_row(model_data: Dict, row: Dict) -> Dict:
    """ create _id dict for row based on several fields """
    result = {}
    if not model_data.get("identity"):
        # if our tbale does not have unique or primary keys
        key_fields = row
    else:
        key_fields = model_data["identity"]
    if "_id" in key_fields:
        del key_fields["_id"]
    for x in key_fields:
        type_ = model_data["columns_data"][x]["type"]
        if type_ in [datetime.datetime, datetime.date]:
            if not isinstance(row[x], str):
                result[x] = row[x].isoformat()
            else:
                result[x] = row[x]
        else:
            result[x] = model_data["columns_data"][x]["type"](row[x])
    result = correct_types(result, model_data["columns_data"], no_default=True)
    return result


def create_obj_id_for_query(id_dict: Dict) -> Text:
    """ create query str based on _id """
    return ",".join([f"{key}={value}" for key, value in id_dict.items()])


def extract_obj_id_from_query(id_row: Text) -> Dict:
    """ reverse _id dict from query str """
    pairs = id_row.split(",")
    _id = {}
    for pair in pairs:
        key, value = pair.split("=")
        _id[key] = value
    return _id


def generate_new_id(base_obj_id: Dict, columns_data: Dict) -> Dict:
    """ generate new id based on previous obj id """
    new_obj_key_dict = {}
    for key, value in base_obj_id.items():
        if columns_data[key]["type"] == str:
            new_obj_key = (
                value
                + f"{'_' if not value.endswith('_') else ''}"
                + uuid.uuid1().hex[5:10]
            )
            len_ = columns_data[key]["len"]
            if len_:
                if new_obj_key[:len_] == value:
                    # if we spend all id previous
                    new_obj_key = new_obj_key[
                        len_ : len_ + len_  # noqa E203
                    ]  # auto format from black
                else:
                    new_obj_key = new_obj_key[:len_]
        elif isinstance(columns_data[key]["db_type"], BigInteger):
            new_obj_key = randint(0, 2 ** 63)
        else:
            logger.error(
                f'unknown logic to generate copy for id of type {columns_data[key]["type"]}'
            )
            new_obj_key = value
        new_obj_key_dict[key] = new_obj_key
    return new_obj_key_dict


def get_changes(old_obj: Dict, new_obj: Dict):
    """ get diff for changes on 'update' for updated object """
    from_ = {}
    to_ = {}
    for key, value in new_obj.items():
        if "_hash" not in key:
            if key not in old_obj:
                to_[key] = value
            elif old_obj[key] != value:
                from_[key] = old_obj[key]
                to_[key] = value
    return {"from": from_, "to": to_}


def get_table_name(model_id: Text) -> Text:
    """ create full table name including schema if it exists """
    return model_id if not cfg.app.db.schema else cfg.app.db.schema + "." + model_id


def parse_db_uri(db_uri: Text) -> None:
    """ parse line of """
    db = dsnparse.parse(db_uri)
    os.environ["SANIC_DB_HOST"] = db.host
    os.environ["SANIC_DB_DATABASE"] = db.database
    os.environ["SANIC_DB_USER"] = db.user
    if db.port:
        os.environ["SANIC_DB_PORT"] = str(db.port)
    os.environ["SANIC_DB_PASSWORD"] = db.password
