import datetime
import logging
import os
import re
from typing import Any, Dict, List, Text
from unicodedata import normalize
from uuid import uuid4

import aiofiles
import yaml
from passlib.hash import pbkdf2_sha256

from gino_admin.config import Config

logger = logging.getLogger("Gino Admin")

salt = uuid4().hex
cfg = Config

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
    "VARCHAR": str,
    "FLOAT": float,
    "DECIMAL": float,
    "NUMERIC": float,
    "DATETIME": datetime.datetime,
    "DATE": datetime.datetime,
    "BOOLEAN": bool,
}


def serialize_obj(obj: Any) -> Any:
    """ method to serialise datetime obj """
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    else:
        return obj


def serialize_dict(container: Dict) -> Dict:
    """ method to serialise datetime in dict """
    for key, value in container.items():
        print(key, value)
        container[key] = serialize_obj(value)
    return container


def reverse_hash_names(hashed_indexes: List, columns_names: List, request_params: Dict):
    for hashed_index in hashed_indexes:
        if columns_names[hashed_index] in request_params:
            request_params[columns_names[hashed_index] + "_hash"] = cfg.hash_method(
                request_params[columns_names[hashed_index]]
            )
            del request_params[columns_names[hashed_index]]
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


def correct_types(params: Dict, columns_data: Dict):
    to_del = []
    for param in params:
        if not params[param]:
            # mean None
            to_del.append(param)
            continue
        if "_hash" not in param and not isinstance(
            params[param], columns_data[param]["type"]
        ):
            if columns_data[param]["type"] is not datetime.datetime:
                params[param] = columns_data[param]["type"](params[param])
            else:
                # todo for date
                params[param] = extract_datetime(params[param])
    for param in to_del:
        del params[param]
    return params


def extract_date(date_str: Text):
    date_object = datetime.datetime.strptime(date_str, "%m-%d-%y")

    return date_object


def extract_datetime(datetime_str: Text):
    for str_format in cfg.datetime_str_formats:
        try:
            datetime_object = datetime.datetime.strptime(datetime_str, str_format)
        except ValueError:
            continue
    return datetime_object


def extract_columns_data(model_id: Text):
    _hash = "_hash"
    column_names = {}
    hashed_indexes = []
    for num, column in enumerate(cfg.app.db.tables[model_id].columns):
        if _hash in column.name:
            column_names[column.name.split(_hash)[0]] = {
                "type": "HASH",
                "nullable": column.nullable,
            }
            hashed_indexes.append(num)
        else:
            db_type = str(column.type).split("(")[0]
            column_names[column.name] = {
                "type": types_map.get(db_type, str),
                "nullable": column.nullable,
            }
    return column_names, hashed_indexes


def generate_token(ip: Text):
    """ generate session token based on user name and salt """
    return pbkdf2_sha256.encrypt(salt + ip)


def read_yaml(preset_file):
    with open(preset_file, "r") as preset_file:
        return yaml.safe_load(preset_file)


def get_presets():
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
