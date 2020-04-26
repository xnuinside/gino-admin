import datetime
from typing import Any, Dict, List

from passlib.hash import pbkdf2_sha256

hash_method = pbkdf2_sha256.encrypt


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


def reverse_hash_names(hashed_indexes: List, columns_names: List, request_params: Dict):
    for hashed_index in hashed_indexes:
        if columns_names[hashed_index] in request_params:
            request_params[columns_names[hashed_index] + "_hash"] = hash_method(
                request_params[columns_names[hashed_index]]
            )
            del request_params[columns_names[hashed_index]]
    return request_params
