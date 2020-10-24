FROM python:3.7.7
RUN pip install poetry==1.0.5
WORKDIR /app
COPY pyproject.toml poetry.lock /app/

# install gino-admin dependencies
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi


# copy gino-admin source code
COPY gino_admin  /app/gino_admin

