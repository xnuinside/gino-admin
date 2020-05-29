Authorization
-------------

1. To disable authorisation:

Set environment variable 'ADMIN_AUTH_DISABLE=1'

.. code-block:: python

    os.environ['ADMIN_AUTH_DISABLE'] = '1'

or from shell:

.. code-block:: python

        export ADMIN_AUTH_DISABLE=1


2. To define admin user & password:

check example/ folder to get code snippets


.. code-block:: python

    app = Sanic()

    app.config["ADMIN_USER"] = "admin"
    app.config["ADMIN_PASSWORD"] = "1234"

