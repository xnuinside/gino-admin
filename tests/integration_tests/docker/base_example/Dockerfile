FROM python:3.7.7 as base
RUN pip install poetry==1.0.5
WORKDIR /app
# hack to avoid reinstall dependencies each time when source code of gino_admin changed
# without it poetry will say error what there is no package gino_admin
RUN  mkdir /app/gino_admin && touch /app/gino_admin/__init__.py
COPY pyproject.toml poetry.lock README.rst /app/

RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

COPY gino_admin  /app/gino_admin

COPY examples/base_example/src /app/
COPY tests/integration_tests/wait_for.py /wait_for.py
CMD python /wait_for.py && python app.py