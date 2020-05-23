API Interface
=============

admin/api/auth
^^^^^^^^^^^^^^
1.1 POST: admin/api/auth

    Auth required to use API endpoints

    To get auth JWT token:

    In request header Authorization provide Basic b64decode login:password stroke

        for user admin:1234
        headers={"Authorization":"Basic YWRtaW46MTIzNA=="}

    Not recommended:
        For fast and easy POC development also allowed provide plain text login:password stroke in Authorization header
        headers={"Authorization":"admin:1234"}

    Response:

.. code-block:: python

        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE1ODkzNzI1MzZ9.IJZG9DV8ZCna7pjK7osUn9veI0Gc47d0Ts5pyGvu6JE"
        }

admin/api/presets
^^^^^^^^^^^^^^^^^
1.2 POST: admin/api/presets

    protected: True (need to provide JWT token in Authorization header)
    Content-type: application/json

    Request body:
        - preset: must contain path to preset '.yml' file
        - drop: flag to Drop DB before upload preset (optional)

Purposes: easy call from tests env when need to drop/create DB from some tests datasets

admin/api/drop_db
^^^^^^^^^^^^^^^^^
1.3 POST: admin/api/drop_db

    protected: True (need to provide JWT token in Authorization header)
    Empty request without body.
    Purposes: Clean up & recreate tables