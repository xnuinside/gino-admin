from typing import List, Text, Tuple, Union

import asyncpg
from sanic.request import Request

from gino_admin import auth, utils
from gino_admin.core import admin, cfg
from gino_admin.history import log_history_event
from gino_admin.routes.logic import (delete_all_by_params, get_by_params,
                                     render_add_or_edit_form,
                                     render_model_view, update_all_by_params)


@admin.route("/<model_id>", methods=["GET"])
@auth.token_validation()
async def model_view_table(
    request: Request, model_id: Text, flash_messages: Union[List[Tuple], Tuple] = None
):
    if "model_id" == "favicon.ico":
        return None
    if flash_messages and not isinstance(flash_messages[0], tuple):
        request.ctx.flash(*flash_messages)
    elif flash_messages:
        for flash in flash_messages:
            request.ctx.flash(*flash)
    return await render_model_view(request, model_id)


@admin.route("/<model_id>/edit", methods=["GET"])
@auth.token_validation()
async def model_edit_view(request, model_id):
    _id = utils.extract_obj_id_from_query(dict(request.query_args)["_id"])
    return await render_add_or_edit_form(request, model_id, _id)


@admin.route("/<model_id>/edit", methods=["POST"])
@auth.token_validation()
async def model_edit_post(request, model_id):
    model_data = cfg.models[model_id]
    model = model_data["model"]
    columns_data = model_data["columns_data"]
    previous_id = utils.extract_obj_id_from_query(dict(request.query_args)["_id"])
    previous_id = utils.correct_types(previous_id, columns_data, no_default=True)
    request_params = {
        key: request.form[key][0] if request.form[key][0] != "None" else None
        for key in request.form
    }
    request_params = utils.prepare_request_params(request_params, model_id, model_data)
    try:
        if not model_data["identity"]:
            old_obj = previous_id
            await update_all_by_params(request_params, previous_id, model)
            obj = request_params
        else:
            obj = await get_by_params(previous_id, model)
            old_obj = obj.to_dict()
            await obj.update(**request_params).apply()
            obj = obj.to_dict()
        changes = utils.get_changes(old_obj, obj)
        new_obj_id = utils.get_obj_id_from_row(model_data, request_params)
        message = f"Object with id {previous_id} was updated."
        if changes:
            message += f'Changes: from {changes["from"]} to {changes["to"]}'
        request.ctx.flash(message, "success")
        log_history_event(request, message, previous_id)
    except asyncpg.exceptions.ForeignKeyViolationError as e:
        request.ctx.flash(
            f"ForeignKey error. "
            f"Impossible to edit field for row {previous_id}, "
            f"because exists objects that depend on it. {e}",
            "error",
        )
    except asyncpg.exceptions.UniqueViolationError:
        request.ctx.flash(
            f"{model_id.capitalize()} with such id already exists", "error"
        )
    except asyncpg.exceptions.NotNullViolationError as e:
        column = e.args[0].split("column")[1].split("violates")[0]
        request.ctx.flash(f"Field {column} cannot be null", "error")
    return await render_add_or_edit_form(request, model_id, new_obj_id)


@admin.route("/<model_id>/add", methods=["GET"])
@auth.token_validation()
async def model_add_view(request, model_id):
    return await render_add_or_edit_form(request, model_id)


@admin.route("/<model_id>/add", methods=["POST"])
@auth.token_validation()
async def model_add(request, model_id):
    model_data = cfg.models[model_id]
    request_params = {key: request.form[key][0] for key in request.form}
    request_params = utils.prepare_request_params(request_params, model_id, model_data)
    not_filled = [x for x in model_data["required_columns"] if x not in request_params]
    if not_filled:
        request.ctx.flash(f"Fields {not_filled} required. Please fill it", "error")
    else:
        try:
            obj = await model_data["model"].create(**request_params)
            obj_id = utils.get_obj_id_from_row(model_data, obj.to_dict())
            message = f"Object with {obj_id} was added."
            request.ctx.flash(message, "success")
            log_history_event(request, message, obj_id)
        except (
            asyncpg.exceptions.StringDataRightTruncationError,
            ValueError,
            asyncpg.exceptions.ForeignKeyViolationError,
        ) as e:
            request.ctx.flash(e.args, "error")
        except asyncpg.exceptions.UniqueViolationError:
            request.ctx.flash(
                f"{model_id.capitalize()} with such id already exists", "error"
            )
        except asyncpg.exceptions.NotNullViolationError as e:
            column = e.args[0].split("column")[1].split("violates")[0]
            request.ctx.flash(f"Field {column} cannot be null", "error")
        except asyncpg.exceptions.UndefinedTableError:
            request.ctx.flash(
                f"Somebody stole the table. Table {model_id} does not exist", "error"
            )

    return await render_add_or_edit_form(request, model_id)


@admin.route("/<model_id>/delete", methods=["POST"])
@auth.token_validation()
async def model_delete(request, model_id):
    """ route for delete item per row """
    model_data = cfg.models[model_id]
    model = model_data["model"]
    request_params = {key: request.form[key][0] for key in request.form}
    obj_id = utils.get_obj_id_from_row(model_data, request_params)
    try:
        if not model_data["identity"]:
            await delete_all_by_params(obj_id, model)
        else:
            obj = await get_by_params(obj_id, model)
            await obj.delete()
        message = f"Object with {obj_id} was deleted"
        flash_message = (message, "success")
        log_history_event(request, message, obj_id)
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
        log_history_event(request, message, f"all, model_id: {model_id}")
    except asyncpg.exceptions.ForeignKeyViolationError as e:
        flash_message = (e.args, "error")
    return await model_view_table(request, model_id, flash_message)
