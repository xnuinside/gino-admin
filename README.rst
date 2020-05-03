gino_admin
----------

|badge1| |badge3| |badge2| 

.. |badge1| image:: https://img.shields.io/pypi/v/gino_admin 
.. |badge2| image:: https://img.shields.io/pypi/l/gino_admin
.. |badge3| image:: https://img.shields.io/pypi/pyversions/gino_admin


Admin Panel for PostgreSQL DB with Gino ORM and Sanic

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/table_view_new.png
  :width: 250
  :alt: Table view

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/table_view_new.png
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
    
    examples/


How to use
----------


Create in your project 'admin.py' file and use `add_admin_panel` from from gino_admin import add_admin_panel


Example:

.. code-block:: python
    
    
    from from gino_admin import add_admin_panel
    
    
    add_admin_panel(
        app, db, [User, Place, City, GiftCard], custom_hash_method=custom_hash_method
    )
        
    
Where:

    'app' - your Sanic application
    'db' : from gino.ext.sanic import Gino; db = Gino() and [User, Place, City, GiftCard] - list of models that you want to add in Admin Panel to maintain
        
    custom_hash_method - optional parameter to define you own hash method to encrypt all '_hash' columns of your Models.
    In admin panel _hash fields will be displayed without '_hash' prefix and fields values will be  hidden like '******'


Or you can use admin as a standalone App, when you need to define Sanic Application first (check 'example' folder)

Version 0.0.7 Updates:
----------------------
1. Fixes: datetime issue in 'Copy' action, delete all modal
2. New feature "Presets" (define multiple CSV files with data - upload all with one click).
3. New feature "Drop DB" (full clean up & recreate tables).

New features can be find under menu with 'Cogs' near 'SQL-Runner' button.

Screen with update.


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


Check examples/src/csv_to_upload for example with presets files.


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


Drop DB
-------

Drop DB feature used for doing full clean up DB - it drop all tables & create them after Drop for all models in Admin Panel.



Upload from CSV
---------------

Files samples for example project can be found here: **examples/src/csv_to_upload**


Version 0.0.6 Updates:
----------------------
1. Clean up template, hide row controls under menu.
2. Added 'Copy' option to DB row.
3. Now errors showed correct in table view pages in process of Delete, Copy, CSV Upload
4. Added possible to work without auth (for Debug purposes). Set env variable 'ADMIN_AUTH_DISABLE=True'
5. Template updated
6. Added export Table's Data to CSV
7. First version of SQL-query execution (run any query and get answer from PostgreSQL)
8. Fixed error display on csv upload



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


