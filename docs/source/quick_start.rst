Quick Start
===========

Installation
------------

First of all you need to install Gino-Admin to your project environment

.. code-block:: console

    $ pip install gino-admin==0.2.3


How to use
----------

You can find several code examples in 'examples' folder - https://github.com/xnuinside/gino-admin/tree/master/examples .


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
Does not matter what Framework used for your main App and that Gino Ext is used to init Gino().

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

