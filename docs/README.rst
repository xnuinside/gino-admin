
Gino-Admin
----------


.. image:: img/logo/g_logo.svg
   :target: img/logo/g_logo.svg
   :alt: Gino-Admin Logo
 

Docs (state: in process): `Gino-Admin docs <https://gino-admin.readthedocs.io/en/latest/ui_screens.html>`_

Play with Demo (current master 0.2.3) `>>>> Gino-Admin demo <<<< <http://www.xnu-im.space/gino_admin_demo/login>`_ (login: admin, pass: 1234)


.. image:: https://img.shields.io/pypi/v/gino_admin
   :target: https://img.shields.io/pypi/v/gino_admin
   :alt: badge1
 
.. image:: https://img.shields.io/pypi/l/gino_admin
   :target: https://img.shields.io/pypi/l/gino_admin
   :alt: badge2
 
.. image:: https://img.shields.io/pypi/pyversions/gino_admin
   :target: https://img.shields.io/pypi/pyversions/gino_admin
   :alt: badge3
 

Admin Panel for PostgreSQL DB with Gino ORM and Sanic


.. image:: img/table_view_new.png
   :target: img/table_view_new.png
   :alt: Table view


.. image:: img/db_presets.png
   :target: img/db_presets.png
   :alt: Load Presets


How to install
^^^^^^^^^^^^^^

.. code-block:: bash


       pip install gino-admin==0.2.4

How to use
^^^^^^^^^^

You can find several code examples in `examples/ <examples/>`_ folder.

Supported features
^^^^^^^^^^^^^^^^^^


* Auth by login/pass with cookie check
* Create(Add new) item by one for the Model
* Delete all rows/per element
* Copy existed element (data table row)
* Edit existed data (table row)
* Search/sort in tables
* Deepcopy element (recursive copy all rows/objects that depend on chosen as ForeignKey)
* `Upload/export data from/to CSV <https://gino-admin.readthedocs.io/en/latest/csv_upload.html#upload-csv-files>`_
* SQL-Runner (execute SQL-queries)
* `Presets: Define order and Load to DB bunch of CSV-files <https://gino-admin.readthedocs.io/en/latest/presets.html>`_
* Init DB (Full clean up behavior: Drop tables & Recreate)
* `Composite CSV: Load multiple relative tables in one CSV-file <https://gino-admin.readthedocs.io/en/latest/csv_upload.html#composite-csv-to-upload>`_
* History logs on changes (log for admin panel actions - edit, delete, add, init_db, load presets and etc)
* Support multiple users for Admin panel (add, edit, remove users from 'Admin Users' page)
* UI Colors customizing

TODO:
^^^^^


* Add possible to add new Presets from GUI
* Select multiple rows for delete
* Copy/deepcopy multiple items
* Edit multiple items (?)
* Roles for Admin Panel users (split accessess)
* Filters in Table's columns
* Other staff on `Gino Project Dashboard <https://github.com/xnuinside/gino-admin/projects/1>`_

Supported Data Types
^^^^^^^^^^^^^^^^^^^^


* JSONB, JSON
* Time, DateTime, Date
* Boolean, String, Decimal, Numeric, Float and etc. 

To see the full list of supported types take a look here: 
`gino_admin/types.py <gino_admin/types.py>`_ 

If you don't see type that you need - open the github issue with request and I will add it https://github.com/xnuinside/gino-admin/issues. Or you can open PR by yourself and I will be glad to review it :) 

How to run Gino-Admin
^^^^^^^^^^^^^^^^^^^^^

Run with Cli
------------

.. code-block:: bash


       gino-admin run #module_name_with_models -d postgresql://%(DB_USER):%(DB_PASSWORD)@%(DB_HOST):%(DB_PORT)/%(DB)

       gino-admin run --help # use to get cli help
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

Example:

.. code-block:: bash


       gino-admin run examples/run_from_cli/src/db.py --db postgresql://gino:gino@localhost:5432/gino -u admin:1234

Run Admin Panel as Standalone App (no matter that framework you use in main app)
--------------------------------------------------------------------------------

You can use Gino Admin as stand alone web app. 
Does not matter what Framework used for your main App and that Gino Ext used to init Gino().

Code example in:  examples/fastapi_as_main_app
How to run example in: examples/fastapi_as_main_app/how_to_run_example.txt

You need to create **admin.py** (for example, you can use any name) to run admin panel:

.. code-block:: python

   import os

   from gino_admin import create_admin_app
   # import module with your models
   import models 

   # gino admin uses Sanic as a framework, so you can define most params as environment variables with 'SANIC_' prefix
   # in example used this way to define DB credentials & login-password to admin panel

   # but you can use 'db_uri' in config to define creds for Database
   # check examples/colored_ui/src/app.py as example 

   os.environ["SANIC_DB_HOST"] = os.getenv("DB_HOST", "localhost")
   os.environ["SANIC_DB_DATABASE"] = "gino"
   os.environ["SANIC_DB_USER"] = "gino"
   os.environ["SANIC_DB_PASSWORD"] = "gino"


   os.environ["SANIC_ADMIN_USER"] = "admin"
   os.environ["SANIC_ADMIN_PASSWORD"] = "1234"

   current_path = os.path.dirname(os.path.abspath(__file__))


   if __name__ == "__main__":
       # host & port - will be used to up on them admin app
       # config - Gino Admin configuration - check docs to see all possible properties,
       # that allow set path to presets folder or custom_hash_method, optional parameter
       # db_models - list of db.Models classes (tables) that you want to see in Admin Panel
       create_admin_app(
           host="0.0.0.0",
           port=os.getenv("PORT", 5000),
           db=models.db,
           db_models=[models.User, models.City, models.GiftCard, models.Country],
           config={
               "presets_folder": os.path.join(current_path, "csv_to_upload")},
       )

All environment variables you can move to define in docker or .env files as you wish, they not needed to be define in '.py', this is just for example shortness.

Add Admin Panel to existed Sanic application as '/admin' route
--------------------------------------------------------------

Create in your project 'admin.py' file and use ``add_admin_panel`` from from gino_admin import add_admin_panel

Code example in:  examples/base_example
How to run example in: examples/base_example/how_to_run_example.txt

Example:

.. code-block:: python


       from from gino_admin import add_admin_panel


       # your app code


       add_admin_panel(
           app, db, [User, Place, City, GiftCard], custom_hash_method=custom_hash_method
       )

Where:


* 'app': your Sanic application
* 'db' : from gino.ext.sanic import Gino; db = Gino() and
* [User, Place, City, GiftCard] - list of models that you want to add in Admin Panel to maintain
* custom_hash_method - optional parameter to define you own hash method to encrypt all '_hash' columns of your Models.

In admin panel _hash fields will be displayed without '_hash' prefix and fields values will be  hidden like '\ ******\ '

Presets
^^^^^^^

Load multiple CSV to DB in order by one click. 
Presets described that CSV-s files and in that order need to be loaded in DB.

Read the docs: `Presets <https://gino-admin.readthedocs.io/en/latest/presets.html>`_

Composite CSV to Upload
^^^^^^^^^^^^^^^^^^^^^^^

Composite CSV - one file that contains data for several relative tables. 

Read the docs: `Composite CSV to Upload <https://gino-admin.readthedocs.io/en/latest/csv_upload.html#composite-csv-to-upload>`_

Config Gino Admin
^^^^^^^^^^^^^^^^^

Read the docs: `Config <https://gino-admin.readthedocs.io/en/latest/config.html>`_

Init DB
^^^^^^^

Init DB feature used for doing full clean up DB - it drop all tables & create them after Drop for all models in Admin Panel.

Upload from CSV
^^^^^^^^^^^^^^^

Files-samples for example project can be found here: **examples/base_example/src/csv_to_upload**

Authorization
^^^^^^^^^^^^^

Read in docs: `Authorization <https://gino-admin.readthedocs.io/en/latest/authorization.html>`_

Limitations
^^^^^^^^^^^

In current version, for correct work of Deepcopy feature in Admin Panel model MUST contain at least one unique or primary_key Column (field).

Screens:
^^^^^^^^

Check in docs: `UI Screens <https://gino-admin.readthedocs.io/en/latest/ui_screens.html>`_

Changelog
---------

**v0.2.5**


#. Added favicon.ico
#. Updated Sanic version (by the way, I plan to move admin panel to FastAPI in next major release)
#. Other dependencies also updated
#. Fixed issue with stop admin panel server

**v0.2.4**


#. Fixed issue with loop from https://github.com/xnuinside/gino-admin/issues/37
