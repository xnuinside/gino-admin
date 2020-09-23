import datetime
import logging
import os
import re
import time
import uuid
from random import randint
from typing import Any, Dict, List, Text, Union
from unicodedata import normalize
from sqlalchemy.types import BigInteger

import aiofiles
import yaml
from passlib.hash import pbkdf2_sha256

from gino_admin import config

cfg = config.cfg
logger = logging.getLogger("Gino Admin")

salt = uuid.uuid4().hex


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

types_map = {
    "INTEGER": int,
    "BIGINT": int,
    "VARCHAR[]": list,
    "SMALLINT": int,
    "VARCHAR": str,
    "FLOAT": float,
    "DECIMAL": float,
    "NUMERIC": float,
    "CHAR": str,
    "TEXT": str,
    "TIMESTAMP": datetime.datetime,
    "DATETIME": datetime.datetime,
    "DATE": datetime.date,
    "BOOLEAN": bool,
}


class GinoAdminError(Exception):
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


class CompositeType:
    pass


def correct_types(params: Dict, columns_data: Dict):
    to_del = []
    for param in params:
        if not params[param]:
            # mean None
            to_del.append(param)
            continue
        if isinstance(param, CompositeType):
            continue
        if "_hash" not in param and not isinstance(
            params[param], columns_data[param]["type"]
        ):
            if columns_data[param]["type"] not in [datetime.datetime, datetime.date]:
                params[param] = columns_data[param]["type"](params[param])
            elif columns_data[param]["type"] == list:
                params[param] = params[param].split(",")
            else:
                params[param] = extract_datetime(params[param], columns_data[param]["type"])
    for param in to_del:
        del params[param]
    for column in columns_data:
        if columns_data[column]["type"] == bool and column not in params:
            params[column] = False
    return params


def extract_date(date_str: Text):
    date_object = datetime.datetime.strptime(date_str, "%m-%d-%y")
    return date_object


def extract_datetime(datetime_str: Text, type_: Union[datetime.datetime, datetime.date]):
    for str_format in cfg.datetime_str_formats:
        try:
            if type_ == datetime.datetime:
                datetime_object = datetime.datetime.strptime(datetime_str, str_format)
                return datetime_object
            elif type_ == datetime.date:
                date_object = datetime.datetime.strptime(datetime_str, str_format).date()
                return date_object
        except ValueError:
            continue


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
    print(row)
    result = {}
    for x in model_data["identity"]:
        print(x)
        print(row[x])
        print(model_data["columns_data"][x]["type"])
        type_ = model_data["columns_data"][x]["type"]
        if type_ in [datetime.datetime, datetime.date]:
            if not isinstance(row[x], str):
                result[x] = row[x].isoformat()
            else:
                result[x] = row[x]
        else:
            result[x] = model_data["columns_data"][x]["type"](row[x]) 
    return result


def generate_new_id(base_key: Text, model_data: Dict) -> Union[Text, int]:
    keys_columns = model_data["identity"]
    if isinstance(base_key, str):
        new_obj_key = (
            base_key
            + f"{'_' if not base_key.endswith('_') else ''}"
            + uuid.uuid1().hex[5:10]
        )
        len_ = model_data["columns_data"][key]["len"]
        if len_:
            if new_obj_key[:len_] == base_key:
                # if we spend all id previous
                new_obj_key = new_obj_key[
                    len_ : len_ + len_  # noqa E203
                ]  # auto format from black
            else:
                new_obj_key = new_obj_key[:len_]
    else:
        if isinstance(model_data["columns_data"][key]["db_type"], BigInteger):
            new_obj_key = randint(0, 2 ** 63)
        else:
            new_obj_key = randint(0, 2 ** 31)
    return new_obj_key


def get_changes(old_obj: Dict, new_obj: Dict):
    from_ = {}
    to_ = {}
    for key, value in new_obj.items():
        if key not in old_obj:
            to_[key] = value
        elif old_obj[key] != value:
            from_[key] = old_obj[key]
            to_[key] = value
    return {"from": from_, "to": to_}

def get_table_name(model_id: Text) -> Text:
    return model_id if not cfg.app.db.schema else cfg.app.db.schema + '.' + model_id