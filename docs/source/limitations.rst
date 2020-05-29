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

