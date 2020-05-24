gino-admin
----------

|badge1| |badge3| |badge2| 

.. |badge1| image:: https://img.shields.io/pypi/v/gino_admin 
.. |badge2| image:: https://img.shields.io/pypi/l/gino_admin
.. |badge3| image:: https://img.shields.io/pypi/pyversions/gino_admin


Admin Panel for PostgreSQL DB with Gino ORM and Sanic

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/table_view_new.png
  :width: 250
  :alt: Table view

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/db_presets.png
  :width: 250
  :alt: Load Presets

How to install
--------------

.. code-block:: python
    
    pip install gino-admin==0.0.10
    


Version 0.0.10 Updates:
-----------------------
1. GinoAdmin Config moved to Pydantic.
Added possible to send any properties to config with config dict. Example:
.. code-block:: python

    add_admin_panel(
        app,
        db,
        [User, Place, City, GiftCard, Country, Item],
        # any Gino Admin Config params you can pass as named params
        custom_hash_method=custom_hash_method,
        presets_folder=os.path.join(current_path, "csv_to_upload"),
        name='Base Example')


2. Added Config param 'name' - this is a name, that will be showed in header near menu.
By Default it is display "Sanic-Gino Admin Panel", now you can change it to your header.

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/custom_header.png

3. UI updates: Gino Admin Panel version now showed in UI footer, Login page now more presentable,
changed index page of Admin Panel, now it presented main feature.

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/custom_header.png

4. Initialised first project's docs

5. Edit/Delete now take object's unique key as argument and stop fall if in key was '/' symbol

6. Added param 'csv_update_existed' in Config. By default 'csv_update_existed = True'. This mean if you upload CSV with rows with unique keys, that already exist in DB - it will update all fields with values from CSV.
You can turn off it with set 'csv_update_existed = False'.


Version 0.0.9 Updates:
----------------------

1. Added New feature: REST API to load DB Presets with token auth.
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


1.2 POST: admin/api/presets

    protected: True (need to provide JWT token in Authorization header)
    Content-type: application/json

    Request body:
        - preset: must contain path to preset '.yml' file
        - drop: flag to Drop DB before upload preset (optional)

Purposes: easy call from tests env when need to drop/create DB from some tests datasets

1.3 POST: admin/api/drop_db

    protected: True (need to provide JWT token in Authorization header)
    Empty request without body.
    Purposes: Clean up & recreate tables

2. New feature: Base Cli interface.

Command in cli:

    **Run Admin Panel from cli**

    gino_admin run #module_name_with_models -d postgresql://%(DB_USER):%(DB_PASSWORD)@%(DB_HOST):%(DB_PORT)/%(DB)

.. code-block:: python

    Optional params:
        -d --db
            Expected format: postgresql://%(DB_USER):%(DB_PASSWORD)@%(DB_HOST):%(DB_PORT)/%(DB)
            Example: postgresql://gino:gino@%gino:5432/gino (based on DB settings in examples/)
            Notice: DB credentials can be set up as  env variables with 'SANIC_' prefix
        -h --host
        -p --port
        -c --config
        --no-auth  Run Admin Panel without Auth in UI
        -u --user Admin User login & password
            Expected format: login:password
            Example: admin:1234
            Notice: user also can be defined from env variable - check Auth section

Example how to use:

.. code-block:: python

        gino-admin run examples/base_example/src/db.py postgresql://gino:gino@%gino:5432/gino -u admin:1234


How to use
----------

You can find several code examples in 'examples' folder.


Run Admin Panel from Command line
#################################

**Run Admin Panel from cli**

.. code-block:: python

    gino_admin run #module_name_with_models -d postgresql://%(DB_USER):%(DB_PASSWORD)@%(DB_HOST):%(DB_PORT)/%(DB)

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

.. code-block:: python

    gino-admin run examples/base_example/src/db.py postgresql://gino:gino@%gino:5432/gino -u admin:1234


Add Admin Panel to existed Sanic application as '/admin' route
##############################################################

Create in your project 'admin.py' file and use `add_admin_panel` from from gino_admin import add_admin_panel

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

* 'app' - your Sanic application
* 'db' : from gino.ext.sanic import Gino; db = Gino() and
* [User, Place, City, GiftCard] - list of models that you want to add in Admin Panel to maintain
* custom_hash_method - optional parameter to define you own hash method to encrypt all '_hash' columns of your Models.

In admin panel _hash fields will be displayed without '_hash' prefix and fields values will be  hidden like '******'

Run Admin Panel as Standalone Sanic app (if you use different frameworks as main App)
#####################################################################################

You can use Gino Admin as stand alone web app. Does not matter what Framework used for your main App.

Code example in:  examples/use_with_any_framework_in_main_app/
How to run example in: examples/use_with_any_framework_in_main_app/how_to_run_example.txt

1. In module where you define DB add 'if block'.
We will use Fast API as main App in our example.

We have db.py where we import Gino as

.. code-block:: python

    from gino.ext.starlette import Gino

    db = Gino(
        dsn='postgresql://gino:gino@localhost:5432/gino'
    )

But if we use this module in Admin Panel we need to have initialisation like this:

.. code-block:: python

    from gino.ext.sanic import Gino
    db = Gino()

To get this, we will add some flag and based on this flag module will init db in needed to as way:
.. code-block:: python

    if os.environ.get('GINO_ADMIN'):
        from gino.ext.sanic import Gino
        db = Gino()
    else:
        from gino.ext.starlette import Gino
        db = Gino(dsn='postgresql://gino:gino@localhost:5432/gino')

So, if now 'db' used by Gino Admin - we use init for Sanic apps, if not - we use for our Main application Framework

Now, we need to create **admin.py** to run admin panel:

.. code-block:: python

    import os

    from gino_admin import create_admin_app

    os.environ["GINO_ADMIN"] = "1"

    # gino admin uses Sanic as a framework, so you can define most params as environment variables with 'SANIC_' prefix
    # in example used this way to define DB credentials & login-password to admin panel

    os.environ["SANIC_DB_HOST"] = "localhost"
    os.environ["SANIC_DB_DATABASE"] = "gino"
    os.environ["SANIC_DB_USER"] = "gino"
    os.environ["SANIC_DB_PASSWORD"] = "gino"


    os.environ["SANIC_ADMIN_USER"] = "admin"
    os.environ["SANIC_ADMIN_PASSWORD"] = "1234"


    if __name__ == "__main__":
        # variable GINO_ADMIN must be set up before import db module, this is why we do import under if __name__
        import db # noqa E402

        # host & port - will be used to up on them admin app
        # config - Gino Admin configuration,
        # that allow set path to presets folder or custom_hash_method, optional parameter
        # db_models - list of db.Models classes (tables) that you want to see in Admin Panel
        create_admin_app(host="0.0.0.0", port=5000, db=db.db, db_models=[db.User, db.City, db.GiftCard])



All environment variables you can move to define in docker or .env files as you wish, they not needed to be define in '.py', this is just for example shortness.


Presets
-------
Load multiple CSV to DB in order by one click.

'Presets' feature allows to define folder with DB presets described in yml format.
Presets described that CSV-s files and in that order

Check also 'example/' folder.


Example:

.. code-block:: python

    name: First Preset
    description: "Init DB with minimal data"
    files:
      users: csv/user.csv
      gifts: csv/gift.csv


Check examples/base_example/src/csv_to_upload for example with presets files.


In order defined in yml, Gino-Admin will load csv files to models.
'files:' describe that file (right sight) must be loaded to the model (left side).

In current example: load data from csv/user.csv to Users table, csv/gift.csv to Gifts.

Don't forget to setup path to folder with presets like with **'presets_folder'** argument.

.. code-block:: python

    ...

    current_path = os.path.dirname(os.path.abspath(__file__))

    add_admin_panel(
        app,
        db,
        [User, Place, City, GiftCard, Country],
        custom_hash_method=custom_hash_method,
        presets_folder=os.path.join(current_path, "csv_to_upload"),
    )

Check example project for more clearly example.

Composite CSV to Upload
-----------------------
Default upload from CSV allows to load CSV with data per table.

Composite CSV files allow to load data for several tables from one CSV files and don't define ForeignKey columns.
You can define table from left to right and if previous table contain ForeignKey for the next table when as linked row will be taken value from current or previous row.
This allow you to define one time Country and 10 cities for it. If it sounds tricky - check example DB schema and XLS example on google docs.

This useful if you want to fill DB with related data, for example, User has some GiftCards (ForeignKey - user.id), GiftCard can be spend to pay off for some Order (ForeignKey - gift_card.id).
So you have set of data that knit together. If you works on some Demo or POC presentation - it's important to keep data consistent, so you want to define 'beautiful data', it's hard if you have 3-4-5 models to define in separate csv.

Composite CSV allow use CSV files with headers with pattern "table_name:column" and also allow to add aliases patterns

Check 'examples/composite_csv_example' code to check DB structure.

And XLS-table sample in Google Sheets:

https://docs.google.com/spreadsheets/d/1ur63acwWExyjWouZ1WEkUxCX73vOcdXzCrEYc7cPhTg/edit?usp=sharing


.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/composite_csv.png
  :width: 250
  :alt: Load Presets


Click - Download -> CSV and you will get result, that can be found in **examples/composite_csv_example/src/csv_to_upload**


Composite CSV can be loaded manual from any Model's Page where exist button 'Upload CSV' - it does not matter from that model you load.

Or you can define preset with Composite CSV and load it as preset. To use composite CSV you need to define key, that started with 'composite' word.

Example:

.. code-block:: python

    name: Composite CSV Preset
    description: "Init DB with data from composite CSV"
    files:
      composite_csv: csv/preset_a/users.csv

'composite_csv: csv/preset_a/users.csv' can be 'composite_any_key: csv/preset_a/users.csv'

You can use multiple composite CSV in one preset.


Config Gino Admin
------------------

You can define in config:

* presets_folder: path where stored predefined DB presets
* custom_hash_method: method that used to hash passwords and other data, that stored as '_hash' columns in DB, by default used pbkdf2_sha256.encrypt
* composite_csv_settings: describe some rules how to parse and load Composite CSV files


composite_csv_settings
######################

composite_csv_settings allow to define multiple tables as one alias

For example, in our example project with composite CSV we have 3 huge different categories separated by tables (they have some different columns) - Camps, Education(courses, lessons, colleges and etc.) and Places(Shopping, Restaurants and etc.)
But we want to avoid duplicate similar columns 3 times, so we can call those 3 tables by one alias name,
for example: 'area' and some column to understand that exactly this is an 'area' - capms, educations or places table for this we need to define 'type_column' we don't use in any model column 'type' so we will use this name for type-column

So, now let's define **composite_csv_settings**

.. code-block:: python

    composite_csv_settings={
        "area": {"models": (Place, Education, Camp), "type_column": "type"}
    }

This mean, when we see in CSV-header 'area' this is data for one of this 3 models, to identify which of this 3 models - check column with header 'area:type'.
In type column values must be same 1-to-1 as table names.

Check source code with example: examples/composite_csv_example

And table sample for it: https://docs.google.com/spreadsheets/d/1ur63acwWExyjWouZ1WEkUxCX73vOcdXzCrEYc7cPhTg/edit?usp=sharing

You also can define table name as 'pattern':

.. code-block:: python

    composite_csv_settings={
        "area": {"models": (SomeModel, SomeModel2, SomeModel3), "pattern": "*_postfix"}
    }

This mean - to understand that this is a DB - take previous table from CSV in row and add '_postfix' at the end.


Drop DB
-------

Drop DB feature used for doing full clean up DB - it drop all tables & create them after Drop for all models in Admin Panel.



Upload from CSV
---------------

Files-samples for example project can be found here: **examples/base_example/src/csv_to_upload**


Authentication
--------------

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


Limitations
-----------

For correct work of Admin Panel all models MUST contain at least one unique and primary_key Column (field).

This column used to identify row (one element) for Copy & Edit & Delete operations.
Name of unique and primary_key column and type does not matter.

So if you define model, for example, User, you can have column **user_id** as unique and primary_key:

.. code-block:: python

    class User(db.Model):

        __tablename__ = "users"

        user_id = db.Column(db.String(), unique=True, primary_key=True)




Or for model 'Country' it can be 'code'

.. code-block:: python

    class Country(db.Model):

        __tablename__ = "countries"

        code = db.Column(db.String(8), unique=True, primary_key=True)
        name = db.Column(db.String())


Supported features
--------------------

- Auth by login/pass with cookie check
- Create(Add new) item by one for the Model
- Search/sort in tables
- Upload/export data from/to CSV
- Delete all rows/per element
- Copy existed element (data table row)
- Edit existed data (table row)
- SQL-Runner (execute SQL-queries)
- Presets: Define order and Load to DB bunch of CSV-files
- Drop DB (Full clean up behavior: Drop tables & Recreate)
- Deepcopy element (recursive copy all rows/objects that depend on chosen as ForeignKey)
- Composite CSV: Load multiple relative tables in one CSV-file


TODO:

- Select multiple for delete/copy
- Edit multiple items (?)
- Roles & User store in DB
- Filters in Table's columns
- History logs on changes (log for admin panel actions)
- Add possible to add new Presets from GUI



Contributions
---------------

Contributions and feature requests are very welcome!


If you have time and want to fix:
Please open issues with that you want to add
or write to me in Telegram: @xnuinside or mail: xnuinside@gmail.com


Developer guide
---------------

Project use pre-commit hooks, so you need setup them

Just run:

.. code-block:: python

    pre-commit install

to install git hooks in your .git/ directory.

How to run integration tests
############################

Run integrations test from  tests/integration_tests/

.. code-block:: console

    cd test/integration_tests

When 2 possible ways.

First way.

.. code-block:: console

    pytest . --docker-compose=test-docker-compose.yml -v

    # will build and run docker compose & execute the tests


Second way (reduce time in process of tests creating/debuggind)

.. code-block:: console

    docker-compose -f test-docker-compose.yml up --build

    # build & run test cluster

    # when in new terminal window:

    pytest . --docker-compose=test-docker-compose.yml --docker-compose-no-build --use-running-containers -v


Screens:
--------

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/table_view_new.png
  :width: 250
  :alt: Table view

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/copy_item.png
  :width: 250
  :alt: Features per row

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/sql_runner.png
  :width: 250
  :alt: SQL-runner

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/add_item.png
  :width: 250
  :alt: Add item

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/auth.png
  :width: 250
  :alt: Simple auth

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/display_errors_on_upload_from_csv.png
  :width: 250
  :alt: Display errors on upload data from CSV

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/db_clean_up.png
  :width: 250
  :alt: DB Drop


