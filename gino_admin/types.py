import datetime

sqlalchemy_types_map = {
    "INTEGER": int,
    "BIGINT": int,
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
    "JSONB": (str, "json"),
    "JSON": (str, "json"),
    "TIME": datetime.time,
    "SMALLINT[]": (list, int),
    "VARCHAR[]": (list, str),
    "INTEGER[]": (list, int),
}


types_map = sqlalchemy_types_map
