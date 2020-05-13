import os

from sanic import response
from sanic.request import Request

from gino_admin.core import api
from gino_admin.routes.logic import (drop_and_recreate_all_tables,
                                     insert_data_from_csv)
from gino_admin.utils import cfg, get_presets, logger, read_yaml


@api.route("/presets", methods=["POST"])
async def presets_use(request: Request):
    # json content/type expected
    preset_path = request.json.get("preset")
    preset_id = request.json.get("preset_id")
    if preset_id:
        presets = get_presets()
        for preset in presets:
            if preset_id == preset["id"]:
                preset = preset
                presets_folder = cfg.presets_folder
                break
        else:
            answer = {
                "error": f"Could not find preset with id {preset_id} in presets folder {cfg.presets_folder}. "
            }
            return response.json(answer, status=422)
    else:
        if not preset_path:
            answer = {
                "error": 'You must provide "preset" field with path to preset yml file or preset_id. '
            }
            return response.json(answer, status=422)
        preset = read_yaml(preset_path)
        presets_folder = os.path.dirname(preset_path)
    if "drop" in request.json:
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
        result = response.json({"status": f"{message}"}, status=200,)
    except FileNotFoundError:
        answer = {"error": f"Wrong file path in Preset {preset['name']}."}
        result = response.json(answer, status=422)
    return result
