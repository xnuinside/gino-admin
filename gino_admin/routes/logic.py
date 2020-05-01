from typing import Text

from sanic.request import Request
from sanic.response import HTTPResponse

from gino_admin.core import cfg, jinja
from gino_admin.utils import extract_columns_data


async def render_model_view(request: Request, model_id: Text) -> HTTPResponse:
    columns_data, hashed_indexes = extract_columns_data(model_id)
    columns_names = list(columns_data.keys())
    model = cfg.app.db.tables[model_id]
    query = cfg.app.db.select([model])
    rows = await query.gino.all()
    output = []
    for row in rows:
        row = {columns_names[num]: field for num, field in enumerate(row)}
        for index in hashed_indexes:
            row[columns_names[index]] = "*************"
        output.append(row)
    output = output[::-1]
    _response = jinja.render(
        "model_view.html",
        request,
        model=model_id,
        columns=columns_names,
        model_data=output,
        objects=cfg.app.db.tables,
        url_prefix=cfg.URL_PREFIX,
    )
    return _response
