gino_admin
----------
Admin Panel for DB with Gino ORM and Sanic (inspired by Flask-Admin)

Work in progress

If you have time and want to fix:
Please open issues with that you want to add
or write to me in Telegram: @xnuinside or mail: xnuinside@gmail.com

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

- Simple auth
- Create item by one for the Model
- Delete all rows


In process:

- Upload rows from csv
- Delete item
- Edit item
- Select multiple for delete
- Edit multiple


Screens:
--------

.. image:: docs/img/auth.png
  :width: 250
  :alt: Simple auth

.. image:: docs/img/add_item.png
  :width: 250
  :alt: Add item

.. image:: docs/img/table_view.png
  :width: 250
  :alt: Table view


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
