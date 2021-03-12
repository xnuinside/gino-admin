import os

from sanic import Blueprint, response
from sanic.request import Request
from sanic_jwt.decorators import protected

from gino_admin import config, utils
from gino_admin.history import log_history_event, write_history_after_response
from gino_admin.routes.logic import (drop_and_recreate_all_tables,
                                     insert_data_from_csv_file,
                                     upload_from_csv_data)
from gino_admin.utils import get_preset_by_id, logger, read_yaml

cfg = config.cfg

api = Blueprint("api", url_prefix=f"{cfg.route}/api")


@api.middleware("request")
async def middleware_request(request):
    request.ctx.flash_messages = []
    request.ctx.history_action = {}


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
            request.ctx.flash_messages = []
            # TODO(ehborisov): handle is_success and errors properly?
            request, is_success = await insert_data_from_csv_file(
                os.path.join(presets_folder, file_path), model_id.lower(), request
            )
        logger.debug(str(request.ctx.flash_messages))
        if "drop" in request.json:
            message = "DB was dropped & Preset was success loaded"
        else:
            message = "Preset was loaded"
        result = response.json({"status": f"{message}"}, status=200)
        log_history_event(
            request,
            f"Loaded preset {preset['id']}{' with DB drop' if with_drop else ''}",
            "system: load_preset",
        )
    except FileNotFoundError:
        answer = {"error": f"Wrong file path in Preset {preset['name']}."}
        result = response.json(answer, status=422)
    return result


@api.route("/init_db", methods=["POST"])
@protected(api)
async def drop(request: Request):
    await drop_and_recreate_all_tables()
    request.ctx.history_action[
        "log_message"
    ] = "Database has been initialized from scratch"
    request.ctx.history_action["object_id"] = "init_db"
    return response.json(
        {"status": "DB has been dropped. Tables re-created."}, status=200
    )


@api.route("/upload_csv", methods=["POST"])
@protected(api)
async def upload_csv(request: Request):
    upload_file = request.files.get("upload_file")
    file_name = utils.secure_filename(upload_file.name)
    model_id = dict(request.query_args).get("model_id")
    if not upload_file or not file_name:
        return response.json(
            {"error": "No file is found in the request payload."}, status=422
        )
    if not file_name.endswith(".csv") or upload_file.type != "text/csv":
        return response.json(
            {"error": "CSV file of text/csv type is expected."}, status=422
        )
    request, is_success = await upload_from_csv_data(
        upload_file, file_name, request, model_id.lower()
    )
    if is_success:
        result = response.json(
            {
                "status": (
                    f"Successfully uploaded {f'model {model_id}' if model_id else 'composite'} data."
                )
            },
            status=200,
        )
    else:
        error = next(
            [m[0] for m in request.ctx.flash_messages if m[1] == "error"], None
        )
        if error:
            return response.json({"error": error}, status=422)
        else:
            return response.json(
                {"error": "Unknown error on csv data upload"}, status=500
            )
    return result
