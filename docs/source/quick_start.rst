Quick Start
===========

Installation
------------

First of all you need to install Gino-Admin to your project environment

.. code-block:: console

    $ pip install gino-admin==0.2.0


How to use
----------

You can find several code examples in 'examples' folder.


Run Admin Panel from Command line
#################################

**Run Admin Panel from cli**

Check Page Command Line interface: `Cli`_

.. _Cli: https://gino-admin.readthedocs.io/en/latest/cli.html

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

