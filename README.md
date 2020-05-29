## Gino-Admin

![Gino-Admin Logo](docs/img/github_gino_admin_logo.png) 

Docs (state: in process): [Gino-Admin docs](https://gino-admin.readthedocs.io/en/latest/ui_screens.html)

Play with Demo (current master 0.0.11a2): [Gino-Admin demo](http://www.xnu-im.space/gino_admin_demo/login)


![badge1](https://img.shields.io/pypi/v/gino_admin) ![badge2](https://img.shields.io/pypi/l/gino_admin) ![badge3](https://img.shields.io/pypi/pyversions/gino_admin) 


Admin Panel for PostgreSQL DB with Gino ORM and Sanic

![Table view](docs/img/table_view_new.png){height=400px width=500px}


.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/db_presets.png
  :width: 250
  :alt: Load Presets


### Supported features

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


##### TODO:

- Select multiple for delete/copy
- Edit multiple items (?)
- Roles & User store in DB
- Filters in Table's columns
- History logs on changes (log for admin panel actions)
- Add possible to add new Presets from GUI
- Other staff on [Gino Project Dashboard](https://github.com/xnuinside/gino-admin/projects/1)


### How to install


.. code-block:: python
    
    pip install gino-admin==0.0.11a2
    

### Updates
#### Version 0.0.11 (current master, not released):
1. Added possibility to define custom route to Gino Admin Panel. With 'route=' config setting
By default, used '/admin' route

2. Added Demo Panel  `Gino-Admin demo`_ - you can log in and play with it. Login & pass - admin / 1234
If you don't see any data in UI maybe somebody before you cleaned it - go to Presets and load one of the data presets.

.. _Gino-Admin demo: http://xnu-in.space/gino_admin_demo

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/demo.png
  :width: 250
  :alt: Load Presets

3. Fixed minors issues: floats now displayed with fixed number of symbols. Parameter can be changed with config param `round_number=`,

Full changelog in [CHANGELOG.txt](CHANGELOG.txt)

### How to use

You can find several code examples in [examples/](examples/) folder.


#### Run Admin Panel from Command line

**Run Admin Panel from cli**


```
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
```

Example:

```gino-admin run examples/base_example/src/db.py postgresql://gino:gino@%gino:5432/gino -u admin:1234
```

#### Add Admin Panel to existed Sanic application as '/admin' route

Create in your project 'admin.py' file and use `add_admin_panel` from from gino_admin import add_admin_panel

Code example in:  examples/base_example
How to run example in: examples/base_example/how_to_run_example.txt

Example:

```
    from from gino_admin import add_admin_panel


    # your app code

    
    add_admin_panel(
        app, db, [User, Place, City, GiftCard], custom_hash_method=custom_hash_method
    )
        
```
    
Where:

* 'app': your Sanic application
* 'db' : from gino.ext.sanic import Gino; db = Gino() and
* [User, Place, City, GiftCard] - list of models that you want to add in Admin Panel to maintain
* custom_hash_method - optional parameter to define you own hash method to encrypt all '_hash' columns of your Models.

In admin panel _hash fields will be displayed without '_hash' prefix and fields values will be  hidden like '******'

#### Run Admin Panel as Standalone Sanic app (if you use different frameworks as main App)

You can use Gino Admin as stand alone web app. Does not matter what Framework used for your main App.

Code example in:  examples/use_with_any_framework_in_main_app/
How to run example in: examples/use_with_any_framework_in_main_app/how_to_run_example.txt

1. In module where you define DB add 'if block'.
We will use Fast API as main App in our example.

We have db.py where we import Gino as
```
    from gino.ext.starlette import Gino

    db = Gino(
        dsn='postgresql://gino:gino@localhost:5432/gino'
    )
```
But if we use this module in Admin Panel we need to have initialisation like this:
```
    from gino.ext.sanic import Gino
    db = Gino()
```

To get this, we will add some flag and based on this flag module will init db in needed to as way:
```

    if os.environ.get('GINO_ADMIN'):
        from gino.ext.sanic import Gino
        db = Gino()
    else:
        from gino.ext.starlette import Gino
        db = Gino(dsn='postgresql://gino:gino@localhost:5432/gino')
```
So, if now 'db' used by Gino Admin - we use init for Sanic apps, if not - we use for our Main application Framework

Now, we need to create **admin.py** to run admin panel:
```
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
```

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

Check: [Config](https://gino-admin.readthedocs.io/en/latest/config.html)



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


