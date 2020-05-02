gino_admin
----------
Admin Panel for PostgreSQL DB with Gino ORM and Sanic

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/table_view_new.png
  :width: 250
  :alt: Table view


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
    'db' : from gino.ext.sanic import Gino; db = Gino() 
        and [User, Place, City, GiftCard] - list of models that you want to add in Admin Panel to maintain
        
    custom_hash_method - optional parameter to define you own hash method to encrypt all '_hash' columns of your Models.
    In admin panel _hash fields will be displayed without '_hash' prefix and fields values will be  hidden like '******'


Or you can use admin as a standalone App, when you need to define Sanic Application first (check 'example' folder)


Version 0.0.6 Updates (not released yet, current master):
----------------------
1. Clean up template, hide row controls under menu.
2. Added 'Copy' option to DB row.
3. Now errors showed correct in table view pages in process of Delete, Copy, CSV Upload
4. Added possible to work without auth (for Debug purposes). Set env variable 'ADMIN_AUTH_DISABLE=True'
5. Template updated
6. Added export Table's Data to CSV
7. First version of SQL-query execution (run any query and get answer from PostgreSQL)
8. Fixed error display on csv upload


Version 0.0.5 Updates
----------------------

1. Upload from CSV: fixed upload from _hash fields - now in step of upload called hash function (same as in edit, or add per item)
2. Fixed errors relative to datetime fields edit, added datetime_str_formats field to Config object, that allows to add custom datetime str formats. They used in step of convert str from DB to datetime object.
3. Now '_hash' fields values in table showed as '***********'
4. Fixed errors relative to int id's. Now they works correct in edit and delete.
5. Update Menu template. Now if there is more when 4 models - they will be available under Dropdown menu.


Version 0.0.4 Updates:
----------------------

1. Upload from CSV - works, added example to `examples/` files. You can upload data from '.csv' tables.
2. Edit per row - now exist button 'edit'.
3. Fixed delete for ALL rows of the model
4. Fixed delete per element.
5. Now works full 'CRUD'.
6. Fixed auth, now it sets 'cookie' and compare user-agent (for multiple users per login)

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

- One user auth
- Create item by one for the Model
- Delete all rows
- Delete one item
- Copy existed element (data table row)
- Edit existed data
- Upload data from csv


TODO:

- Select multiple for delete/copy
- Deepcopy element (recursive copy all rows/objects that depend on chosen as ForeignKey)
- Edit multiple
- Multiple users
- Set up data presets (drop table for some data state, defined from csv)
- Filters in columns
- Actions history



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

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/table_view_new.png
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


