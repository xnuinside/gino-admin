from typing import List, Text, Tuple, Union
from ast import literal_eval
import asyncpg
from sanic.request import Request
import datetime
from gino_admin import auth, utils
from gino_admin.core import admin, cfg
from gino_admin.routes.logic import render_add_or_edit_form, render_model_view


@admin.route("/<model_id>", methods=["GET"])
@auth.token_validation()
async def model_view_table(
    request: Request, model_id: Text, flash_messages: Union[List[Tuple], Tuple] = None
):
    if flash_messages and not isinstance(flash_messages[0], tuple):
        request["flash"](*flash_messages)
    elif flash_messages:
        for flash in flash_messages:
            request["flash"](*flash)
    return await render_model_view(request, model_id)


@admin.route("/<model_id>/edit", methods=["GET"])
@auth.token_validation()
async def model_edit_view(request, model_id):
    _id = dict(request.query_args)["_id"]
    
    print(_id)
    _id = literal_eval(_id)
    return await render_add_or_edit_form(request, model_id, _id)


@admin.route("/<model_id>/edit", methods=["POST"])
@auth.token_validation()
async def model_edit_post(request, model_id):
    model_data = cfg.models[model_id]
    model = model_data["model"]
    request_params = {
        key: request.form[key][0] if request.form[key][0] != "None" else None
        for key in request.form
    }
    obj_id = utils.get_obj_id_from_row(model_data, request_params)
    obj_id = utils.correct_types(obj_id, model_data["columns_data"])
    print(obj_id)
    obj = await model.get(**obj_id)
    old_obj = obj.to_dict()
    if model_data["hashed_indexes"]:
        request_params = utils.reverse_hash_names(model_id, request_params)
    request_params = utils.correct_types(request_params, model_data["columns_data"])
    try:
        await obj.update(**request_params).apply()
        changes = utils.get_changes(old_obj, obj.to_dict())
        message = f'Object with id {obj_id} was updated. Changes: from {changes["from"]} to {changes["to"]}'
        request["flash"](message, "success")
        request["history_action"]["log_message"] = message
        request["history_action"]["object_id"] = obj_id
    except asyncpg.exceptions.ForeignKeyViolationError:
        request["flash"](
            f"ForeignKey error. "
            f"Impossible to edit {model_data['key']} field for row {obj_id}, "
            f"because exists objects that depend on it. ",
            "error",
        )
        request_params.update(obj_id)
    except asyncpg.exceptions.UniqueViolationError:
        request["flash"](
            f"{model_id.capitalize()} with such id already exists", "error"
        )
    except asyncpg.exceptions.NotNullViolationError as e:
        column = e.args[0].split("column")[1].split("violates")[0]
        request["flash"](f"Field {column} cannot be null", "error")
    return await render_add_or_edit_form(
        request, model_id, obj_id
    )


@admin.route("/<model_id>/add", methods=["GET"])
@auth.token_validation()
async def model_add_view(request, model_id):
    return await render_add_or_edit_form(request, model_id)


@admin.route("/<model_id>/add", methods=["POST"])
@auth.token_validation()
async def model_add(request, model_id):
    model_data = cfg.models[model_id]
    request_params = {key: request.form[key][0] for key in request.form}
    not_filled = [x for x in model_data["required_columns"] if x not in request_params]
    if not_filled:
        request["flash"](f"Fields {not_filled} required. Please fill it", "error")
    else:
        if model_data["hashed_indexes"]:
            request_params = utils.reverse_hash_names(model_id, request_params)
        try:
            request_params = utils.correct_types(
                request_params, model_data["columns_data"]
            )
            print(request_params, 'after format')
            obj = await model_data["model"].create(**request_params)
            message = f'Object with {model_data["key"]} {obj.to_dict()[model_data["key"]]} was added.'
            request["flash"](message, "success")
            request["history_action"]["log_message"] = message
            request["history_action"]["object_id"] = obj.to_dict()[model_data["key"]]
        except (
            asyncpg.exceptions.StringDataRightTruncationError,
            ValueError,
            asyncpg.exceptions.ForeignKeyViolationError,
        ) as e:
            request["flash"](e.args, "error")
        except asyncpg.exceptions.UniqueViolationError:
            request["flash"](
                f"{model_id.capitalize()} with such id already exists", "error"
            )
        except asyncpg.exceptions.NotNullViolationError as e:
            column = e.args[0].split("column")[1].split("violates")[0]
            request["flash"](f"Field {column} cannot be null", "error")

    return await render_add_or_edit_form(request, model_id)


@admin.route("/<model_id>/delete", methods=["POST"])
@auth.token_validation()
async def model_delete(request, model_id):
    """ route for delete item per row """
    model_data = cfg.models[model_id]
    request_params = {key: request.form[key][0] for key in request.form}
    # unique_column_name
    unique_cn = model_data["key"]
    request_params[unique_cn] = model_data["columns_data"][unique_cn]["type"](
        request_params[unique_cn]
    )

    try:
        await model_data["model"].delete.where(
            getattr(model_data["model"], unique_cn) == request_params[unique_cn]
        ).gino.status()
        message = f"Object with {unique_cn} {request_params[unique_cn]} was deleted"
        flash_message = (message, "success")
        request["history_action"]["log_message"] = message
        request["history_action"]["object_id"] = request_params[unique_cn]
    except asyncpg.exceptions.ForeignKeyViolationError as e:
        flash_message = (str(e.args), "error")

    return await model_view_table(request, model_id, flash_message)


@admin.route("/<model_id>/delete_all", methods=["POST"])
@auth.token_validation()
async def model_delete_all(request, model_id):
    try:
        await cfg.models[model_id]["model"].delete.where(True).gino.status()
        message = f"All objects in {model_id} was deleted"
        flash_message = (message, "success")
        request["history_action"]["log_message"] = message
        request["history_action"]["object_id"] = model_id
    except asyncpg.exceptions.ForeignKeyViolationError as e:
        flash_message = (e.args, "error")
    return await model_view_table(request, model_id, flash_message)
