FROM python:3.7.7 as base
WORKDIR /app
COPY examples/fastapi_as_main_app/requirements.txt /app/requirements.txt
RUN pip install gino==1.0.0 && \
    pip install gino-starlette==0.1.1 && \
    pip install fastapi==0.54.1 && \
    pip install uvicorn==0.11.5
COPY examples/fastapi_as_main_app/src/main.py examples/fastapi_as_main_app/src/db.py /app/
COPY tests/integration_tests/wait_for.py /wait_for.py
CMD python /wait_for.py && uvicorn main:app  --host 0.0.0.0 --port 5050