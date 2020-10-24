FROM local/gino_admin_common_tests
# copy example source code
COPY examples/colored_ui/src /app/

COPY tests/integration_tests/docker/wait_for.py /wait_for.py
CMD python /wait_for.py && python app.py