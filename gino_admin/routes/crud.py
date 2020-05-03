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
    columns_data, hashed_indexes = utils.extract_columns_data(model_id)
    columns_names = list(columns_data.keys())
    model = cfg.models[model_id]
    # id can be str or int
    obj_id = columns_data["id"]["type"](obj_id)
    obj = utils.serialize_dict((await model.get(obj_id)).to_dict())
    return jinja.render(
        "add_form.html",
        request,
        model=model_id,
        obj=obj,
        objects=cfg.models,
        columns_names=columns_names,
        url_prefix=cfg.URL_PREFIX,
    )


@admin.route("/<model_id>/<obj_id>/edit", methods=["POST"])
@auth.token_validation()
async def model_edit_post(request, model_id, obj_id):
    columns_data, hashed_indexes = utils.extract_columns_data(model_id)
    columns_names = list(columns_data.keys())
    model = cfg.models[model_id]
    obj = await model.get(columns_data["id"]["type"](obj_id))
    request_params = {
        key: request.form[key][0] if request.form[key][0] != "None" else None
        for key in request.form
    }
    if hashed_indexes:
        request_params = utils.reverse_hash_names(
            hashed_indexes, columns_names, request_params
        )
    request_params = utils.correct_types(request_params, columns_data)
    if hashed_indexes:
        request_params = utils.reverse_hash_names(
            hashed_indexes, columns_names, request_params
        )
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
        columns_names=columns_names,
        url_prefix=cfg.URL_PREFIX,
        url=f"{cfg.URL_PREFIX}/{model_id}/{obj_id}/edit",
    )


@admin.route("/<model>/add", methods=["GET"])
@auth.token_validation()
async def model_add_view(request, model):
    columns_data, hashed_indexes = utils.extract_columns_data(model)
    columns_names = list(columns_data.keys())
    response = jinja.render(
        "add_form.html",
        request,
        model=model,
        add=True,
        obj={},
        columns_names=columns_names,
        objects=cfg.models,
        url_prefix=cfg.URL_PREFIX,
    )
    return response


@admin.route("/<model>/add", methods=["POST"])
@auth.token_validation()
async def model_add(request, model):
    columns_data, hashed_indexes = utils.extract_columns_data(model)
    required = [
        key for key, value in columns_data.items() if value["nullable"] is False
    ]
    columns_names = list(columns_data.keys())
    request_params = {key: request.form[key][0] for key in request.form}
    not_filled = [x for x in required if x not in request_params]
    if not_filled:
        request["flash"](f"Fields {not_filled} required. Please fill it", "error")
    else:
        if hashed_indexes:
            request_params = utils.reverse_hash_names(
                hashed_indexes, columns_names, request_params
            )
        try:
            request_params = utils.correct_types(request_params, columns_data)
            await cfg.models[model].create(**request_params)
            request["flash"]("Object was added", "success")
        except (
            asyncpg.exceptions.StringDataRightTruncationError,
            ValueError,
            asyncpg.exceptions.ForeignKeyViolationError,
        ) as e:
            request["flash"](e.args, "error")
        except asyncpg.exceptions.UniqueViolationError:
            request["flash"](
                f"{model.capitalize()} with such id already exists", "error"
            )
        except asyncpg.exceptions.NotNullViolationError as e:
            column = e.args[0].split("column")[1].split("violates")[0]
            request["flash"](f"Field {column} cannot be null", "error")

    return jinja.render(
        "add_form.html",
        request,
        model=model,
        objects=cfg.models,
        obj={},
        columns_names=columns_names,
        url_prefix=cfg.URL_PREFIX,
    )


@admin.route("/<model_id>/delete", methods=["POST"])
@auth.token_validation()
async def model_delete(request, model_id):
    """ route for delete item per row """
    request_params = {key: request.form[key][0] for key in request.form}
    columns_data, hashed_indexes = utils.extract_columns_data(model_id)
    request_params["id"] = columns_data["id"]["type"](request_params["id"])
    try:
        await cfg.models[model_id].delete.where(
            cfg.models[model_id].id == request_params["id"]
        ).gino.status()
        request["flash"](f"Object with {request_params['id']} was deleted", "success")
    except asyncpg.exceptions.ForeignKeyViolationError as e:
        request["flash"](e.args, "error")
    return await render_model_view(request, model_id)


@admin.route("/<model_id>/delete_all", methods=["POST"])
@auth.token_validation()
async def model_delete_all(request, model_id):
    try:
        await cfg.models[model_id].delete.where(True).gino.status()
        request["flash"]("All objects was deleted", "success")
    except asyncpg.exceptions.ForeignKeyViolationError as e:
        request["flash"](e.args, "error")
    return await render_model_view(request, model_id)
