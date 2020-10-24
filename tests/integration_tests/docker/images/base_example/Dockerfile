FROM local/gino_admin_common_tests
# copy example source code
COPY examples/base_example/requirements.txt /app/
COPY examples/base_example/src /app/

# install example requirements
RUN pip install -r requirements.txt

COPY tests/integration_tests/docker/wait_for.py /wait_for.py
CMD python /wait_for.py && python app.py