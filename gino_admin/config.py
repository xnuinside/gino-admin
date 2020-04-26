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
    session = {}
    # upload from csv config
    upload_dir = "files/"
    max_file_size = 10485760
    allowed_file_types = ["csv"]
