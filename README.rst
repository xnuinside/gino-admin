gino_admin
----------
Admin Panel for DB with Gino ORM and Sanic (inspired by Flask-Admin)

Work in progress

If you have time and want to fix:
Please open issues with that you want to add
or write to me in Telegram: @xnuinside or mail: xnuinside@gmail.com



Version 0.0.5 Updates:
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



Limitations
-----------

For correct work of Admin Panel all models MUST contain unique 'id' field.
'id' used to identify row (one element) for Edit & Delete operations.

so if you define model, for example, User:

.. code-block:: python

    class User(db.Model):

        __tablename__ = "users"

        id = db.Column(db.String(), unique=True, primary_key=True)


Supported operations
--------------------

- One user auth
- Create item by one for the Model
- Delete all rows
- Delete one item
- Edit existed data
- Upload data from csv


TODO:

- Select multiple for delete
- Edit multiple
- Multiple users
- Set up data presets (drop table for some data state, defined from csv)
- Filters in columns
- Actions history


Screens:
--------

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/auth.png
  :width: 250
  :alt: Simple auth

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/add_item.png
  :width: 250
  :alt: Add item

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/table_view.png
  :width: 250
  :alt: Table view

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/csv_upload.png
  :width: 250
  :alt: Add rows from CSV upload


Contributions
---------------

Contributions and feature requests are very welcome!


Developer guide
_______________

Project use pre-commit hooks, so you need setup them

Just run:

.. code-block:: python

    pre-commit install

to install git hooks in your .git/ directory.
