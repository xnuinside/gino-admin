import os

from gino_admin.core import add_admin_panel  # noqa F401
# load routes
from gino_admin.routes import crud  # noqa F401
from gino_admin.routes import main  # noqa F401

os.environ["ADMIN_AUTH_DISABLE"] = "1"
