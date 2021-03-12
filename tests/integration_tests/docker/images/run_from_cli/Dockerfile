FROM local/gino_admin_common_tests
# copy example source code
COPY examples/run_from_cli/src/db.py /app/
COPY tests/integration_tests/docker/wait_for.py /wait_for.py

# run
RUN ls -la
RUN mkdir /app/docs/ && touch /app/docs/README.rst
CMD python /wait_for.py && \
    gino-admin run /app/db.py --db postgresql://gino:gino@postgres:5432/gino -u admin:1234 -p 5060