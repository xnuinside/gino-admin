import os

from sanic import Blueprint, response
from sanic.request import Request
from sanic_jwt.decorators import protected

from gino_admin import config
from gino_admin.history import write_history_after_response
from gino_admin.routes.logic import (drop_and_recreate_all_tables,
                                     insert_data_from_csv)
from gino_admin.utils import get_preset_by_id, logger, read_yaml

cfg = config.cfg

api = Blueprint("api", url_prefix=f"{cfg.route}/api")


@api.middleware("request")
async def middleware_request(request):
    request["flash_messages"] = []
    request["history_action"] = {}


@api.middleware("response")
async def middleware_response(request, response):
    if request.endpoint in cfg.track_history_endpoints and request.method == "POST":
        await write_history_after_response(request)


@api.route("/presets", methods=["POST"])
@protected(api)
async def presets(request: Request):
    # json content/type expected
    preset_path = request.json.get("preset")
    preset_id = request.json.get("preset_id")
    if preset_id:
        preset = get_preset_by_id(preset_id)
        if not preset:
            answer = {
                "error": f"Could not find preset with id {preset_id} in presets folder {cfg.presets_folder}. "
            }
            return response.json(answer, status=422)
        presets_folder = cfg.presets_folder
    else:
        if not preset_path:
            answer = {
                "error": 'You must provide "preset" field with path to preset yml file or preset_id. '
            }
            return response.json(answer, status=422)
        preset = read_yaml(preset_path)
        presets_folder = os.path.dirname(preset_path)
    with_drop = "drop" in request.json
    if with_drop:
        await drop_and_recreate_all_tables()
    try:
        for model_id, file_path in preset["files"].items():
            request["flash_messages"] = []
            request, code = await insert_data_from_csv(
                os.path.join(presets_folder, file_path), model_id.lower(), request
            )
        logger.debug(str(request["flash_messages"]))
        if "drop" in request.json:
            message = "DB was dropped & Preset was success loaded"
        else:
            message = "Preset was loaded"
        result = response.json({"status": f"{message}"}, status=200)

        request["history_action"]["log_message"] = (
            f"Loaded preset {preset['id']}"
            f"" + f"{' with DB drop' if with_drop else ''}"
        )
        request["history_action"]["object_id"] = "load_preset"
    except FileNotFoundError:
        answer = {"error": f"Wrong file path in Preset {preset['name']}."}
        result = response.json(answer, status=422)
    return result


@api.route("/init_db", methods=["POST"])
@protected(api)
async def drop(request: Request):
    await drop_and_recreate_all_tables()
    request["history_action"]["log_message"] = "DB was Init from Scratch"
    request["history_action"]["object_id"] = "init_db"
    return response.json({"status": "DB was dropped. Tables re-created."}, status=200)
