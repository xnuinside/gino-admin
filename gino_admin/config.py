from expiring_dict import ExpiringDict
from passlib.hash import pbkdf2_sha256


class App:
    """ class to store links to main app data app.config and DB"""

    config = {}
    db = None


class Config:
    """ Gino Admin Panel settings """

    URL_PREFIX = "/admin"
    app = App
    hash_method = pbkdf2_sha256.encrypt
    models = {}
    sessions = ExpiringDict(ttl=3600)
    # upload from csv config
    upload_dir = "files/"
    max_file_size = 10485760
    allowed_file_types = ["csv"]
    datetime_str_formats = [
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S.%f",
        "%m-%d-%yT%H:%M:%S.%f",
        "%m-%d-%y %H:%M:%S",
    ]
    presets_folder = "presets"
    composite_csv_settings = "no settings"
