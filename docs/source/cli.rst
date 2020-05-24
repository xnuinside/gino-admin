Cli
======================


Run Gino Admin Panel with Cli

.. code-block:: python

    gino_admin run #module_name_with_models -d postgresql://%(DB_USER):%(DB_PASSWORD)@%(DB_HOST):%(DB_PORT)/%(DB)

Example:

.. code-block:: python

    gino-admin run examples/base_example/src/db.py postgresql://gino:gino@%gino:5432/gino -u admin:1234


.. code-block:: python

    Optional params:
        -d --db
            Expected format: postgresql://%(DB_USER):%(DB_PASSWORD)@%(DB_HOST):%(DB_PORT)/%(DB)
            Example: postgresql://gino:gino@%gino:5432/gino (based on DB settings in examples/)
            Notice: DB credentials can be set up as  env variables with 'SANIC_' prefix
        -h --host
        -p --port
        -c --config Example:  -c "presets_folder=examples/base_example/src/csv_to_upload;some_property=1"
                    Notice: all fields that not supported in config will be ignored, like 'some_property' in example
        --no-auth  Run Admin Panel without Auth in UI
        -u --user Admin User login & password
            Expected format: login:password
            Example: admin:1234
            Notice: user also can be defined from env variable with 'SANIC_' prefix - check Auth section example


