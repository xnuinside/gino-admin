import asyncpg

from gino_admin import auth, utils
from gino_admin.core import admin, cfg, jinja
from gino_admin.routes.logic import render_model_view


@admin.route("/<model_id>", methods=["GET"])
@auth.token_validation()
async def model_view_table(request, model_id):
    return await render_model_view(request, model_id)


@admin.route("/<model_id>/<obj_id>/edit", methods=["GET"])
@auth.token_validation()
async def model_edit_view(request, model_id, obj_id):
    model_data = cfg.models[model_id]
    model = cfg.models[model_id]["model"]
    # id can be str or int
    obj_id = model_data["columns_data"]["id"]["type"](obj_id)
    obj = utils.serialize_dict((await model.get(obj_id)).to_dict())
    return jinja.render(
        "add_form.html",
        request,
        model=model_id,
        obj=obj,
        objects=cfg.models,
        columns_names=model_data["columns_names"],
        url_prefix=cfg.URL_PREFIX,
    )


@admin.route("/<model_id>/<obj_id>/edit", methods=["POST"])
@auth.token_validation()
async def model_edit_post(request, model_id, obj_id):
    model_data = cfg.models[model_id]
    model = model_data["model"]
    obj = await model.get(model_data["columns_data"]["id"]["type"](obj_id))
    request_params = {
        key: request.form[key][0] if request.form[key][0] != "None" else None
        for key in request.form
    }
    request_params = utils.correct_types(request_params, model_data["columns_data"])
    if model_data["hashed_indexes"]:
        request_params = utils.reverse_hash_names(model_id, request_params)
    try:
        await obj.update(**request_params).apply()
        obj = obj.to_dict()
    except asyncpg.exceptions.UniqueViolationError:
        request["flash"](
            f"{model_id.capitalize()} with such id already exists", "error"
        )
    except asyncpg.exceptions.NotNullViolationError as e:
        column = e.args[0].split("column")[1].split("violates")[0]
        request["flash"](f"Field {column} cannot be null", "error")
    return jinja.render(
        "add_form.html",
        request,
        model=model_id,
        obj=obj,
        objects=cfg.models,
        columns_names=model_data["columns_names"],
        url_prefix=cfg.URL_PREFIX,
        url=f"{cfg.URL_PREFIX}/{model_id}/{obj_id}/edit",
    )


@admin.route("/<model_id>/add", methods=["GET"])
@auth.token_validation()
async def model_add_view(request, model_id):
    response = jinja.render(
        "add_form.html",
        request,
        model=model_id,
        add=True,
        obj={},
        columns_names=cfg.models[model_id]["columns_names"],
        objects=cfg.models,
        url_prefix=cfg.URL_PREFIX,
    )
    return response


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
            await model_data["model"].create(**request_params)
            request["flash"]("Object was added", "success")
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

    return jinja.render(
        "add_form.html",
        request,
        model=model_id,
        objects=cfg.models,
        obj={},
        columns_names=model_data["columns_names"],
        url_prefix=cfg.URL_PREFIX,
    )


@admin.route("/<model_id>/delete", methods=["POST"])
@auth.token_validation()
async def model_delete(request, model_id):
    """ route for delete item per row """
    model_data = cfg.models[model_id]
    request_params = {key: request.form[key][0] for key in request.form}
    # todo: move to normal feature
    _id_field = "id" if request_params.get("id") else "token"
    request_params[_id_field] = model_data["columns_data"][_id_field]["type"](
        request_params[_id_field]
    )
    try:
        await model_data["model"].delete.where(
            getattr(model_data["model"], _id_field) == request_params[_id_field]
        ).gino.status()
        request["flash"](
            f"Object with {_id_field} {request_params[_id_field]} was deleted",
            "success",
        )
    except asyncpg.exceptions.ForeignKeyViolationError as e:
        request["flash"](e.args, "error")
    return await render_model_view(request, model_id)


@admin.route("/<model_id>/delete_all", methods=["POST"])
@auth.token_validation()
async def model_delete_all(request, model_id):
    try:
        await cfg.models[model_id]["model"].delete.where(True).gino.status()
        request["flash"]("All objects was deleted", "success")
    except asyncpg.exceptions.ForeignKeyViolationError as e:
        request["flash"](e.args, "error")
    return await render_model_view(request, model_id)
