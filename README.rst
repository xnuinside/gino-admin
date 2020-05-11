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
    
    pip install gino_admin
    

Usage example
-------------

Full example placed in 'examples' folder:

.. code-block:: python
    
    examples/base_example/


How to use
----------
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

We have db.py where we import Gino as:

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
        db = Gino(
            dsn='postgresql://gino:gino@localhost:5432/gino'
        )

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


Version 0.0.8 Updates:
----------------------
1. Added more possibilities to use Gino Admin with applications in different frameworks (Fast API, or aiohttp, or any others)
1.1 Added example how to Gino Admin if main application developed with different Framework (Fast API or smth else)

Example in **examples/use_with_any_framework_in_main_app**

1.2 added **create_admin_app** method to full init admin app as separate server

1.3 Old example moved to **base_example/** folder

1.4 in method 'init_admin_app' argument 'gino_models' was renamed to 'db_models'

3. Added support for columns with different names can be used as 'id'
- now Admin Panel checks 'unique' flag in the column.
If model does not have 'unique' column - it will not showed in admin panel
and you will see error message about it at the start and in logs.

4. Added Feature "Combined data upload" - possibility to define one CSV files, that contains several relative tables.
Used special to prepare dataset for demo purposes or tests. When it more effective and fast to define
relative data in one file.

Example with CSVs samples added to

5. Fixed issue with Logout.



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

Configure Gino Admin
--------------------

You can define in config:

* presets_folder: path where stored predefined DB presets
* custom_hash_method: method that used to hash passwords and other data, that stored as *_hash columns in DB,
    by default used pbkdf2_sha256.encrypt


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

For correct work of Admin Panel all models MUST contain unique 'id' field.
'id' used to identify row (one element) for Edit & Delete operations.

so if you define model, for example, User:

.. code-block:: python

    class User(db.Model):

        __tablename__ = "users"

        id = db.Column(db.String(), unique=True, primary_key=True)

id also can be Integer/BigInteger:


.. code-block:: python

    class User(db.Model):

        __tablename__ = "users"

        id = db.Column(db.BigInteger(), unique=True, primary_key=True)


Supported operations
--------------------

- Auth by login/pass with cookie check
- Create(Add new) item by one for the Model
- Search/sort in tables
- Upload/export data from/to CSV
- Delete all rows/per element
- Copy existed element (data table row)
- Edit existed data (table row)
- SQL-Runner (execute SQL-queries)
- Load DB Presets (bunch of CSV)
- Drop DB (Full clean up behavior: Drop tables & Recreate)


TODO:

- Select multiple for delete/copy
- Deepcopy element (recursive copy all rows/objects that depend on chosen as ForeignKey)
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
_______________

Project use pre-commit hooks, so you need setup them

Just run:

.. code-block:: python

    pre-commit install

to install git hooks in your .git/ directory.


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


