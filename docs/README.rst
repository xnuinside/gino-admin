
Gino-Admin
----------


.. image:: img/logo/g_logo.svg
   :target: img/logo/g_logo.svg
   :alt: Gino-Admin Logo
 

Docs (state: in process): `Gino-Admin docs <https://gino-admin.readthedocs.io/en/latest/ui_screens.html>`_

Play with Demo (current master 0.2.1) `>>>> Gino-Admin demo <<<< <http://www.xnu-im.space/gino_admin_demo/login>`_ (login: admin, pass: 1234)


.. image:: https://img.shields.io/pypi/v/gino_admin
   :target: https://img.shields.io/pypi/v/gino_admin
   :alt: badge1
 
.. image:: https://img.shields.io/pypi/l/gino_admin
   :target: https://img.shields.io/pypi/l/gino_admin
   :alt: badge2
 
.. image:: https://img.shields.io/pypi/pyversions/gino_admin
   :target: https://img.shields.io/pypi/pyversions/gino_admin
   :alt: badge3
 

Admin Panel for PostgreSQL DB with Gino ORM and Sanic


.. image:: img/table_view_new.png
   :target: img/table_view_new.png
   :alt: Table view


.. image:: img/db_presets.png
   :target: img/db_presets.png
   :alt: Load Presets


How to install
^^^^^^^^^^^^^^

.. code-block:: bash


       pip install gino-admin==0.2.1

How to use
^^^^^^^^^^

You can find several code examples in `examples/ <examples/>`_ folder.

Updates in version 0.2.1 (current master):
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


#. Fixes:

1.1 Dependencies - removed unnecessary packages and added one lost for cli. Cli now works correct. 
1.2 Login form now provide errors if you enter wrong user or passoword
1.3 Wrong attepts to login in Admin panel are adding to History now


#. Added possibility to customize UI colors with config. 

Default colors schema also changed:


.. image:: img/new_colors.png
   :target: img/new_colors.png
   :alt: Table view


Config object now has section 'ui'. In UI section now exist 'colors' where you can set up colors that will be used for:


* Primary buttons. Property: buttons
* Second buttons. Property: buttons_second
* Alert buttons (actions that something remove/reset - deleted, drop db and etc). Property: buttons_alert
* Tables headers. Property: table
* Tables with Alert headers (like in Init DB). Property: table_alerts
* Footer background. Property: footer
* Header background. Property: header

Admin panel used SemanticUI as CSS Framework so all names of possible colors is described and showed here:
https://semantic-ui.com/usage/theming.html 

(red: #B03060; orange #FE9A76; yellow: #FFD700; olive:  #32CD32 green:  #016936; teal :  #008080; blue :  #0E6EB8; violet: #EE82EE; purple: #B413EC; pink:  #FF1493; brown:  #A52A2A; grey :  #A0A0A0; black:  #000000;)

To change colors pass config as:

.. code-block:: python


   create_admin_app(
           host="0.0.0.0",
           port=os.getenv("PORT", 5000),
           db=example.models.db,
           db_models=db_models,
           config={
               "ui" : {
                   "colors": 
                   {"buttons": "orange",
                   "buttons_alert": "pink"}
                   },
               "db_uri": "postgresql://gino:gino@localhost:5432/gino"
           },
       )

Example here: examples/colored_ui/


#. 
   Added example how to add all models from file with one method (to avoid import each model separate) - palced in *examples/colored_ui/src/app.py* method - **create_models_list**

#. 
   Added valid input for Text columns as Text Area

   .. image:: img/text_area.png
      :target: img/text_area.png
      :alt: Text Area Inouts


Updates in version 0.2.0:
^^^^^^^^^^^^^^^^^^^^^^^^^


#. **UI fixes**\ : 


* Data Picker was fixed, required fields now dispalayed with '* required' in UI.
* Menu in header became scrollable, now you can see 20+ models without pain
* Tables became scrollable horisontal - you can keep dozen columns and see them (hooray!)
* in Add/edit forms now displayd the field type


#. **Major changes**\ : 


* **Limitation to have 'unique' rows was removed**. Now you not need any unique keys to make possible work with table in Admin panel. Just keep in mind that if you edit row - you will also edit all full 'dublicated' rows. So we try identify row by all fields. 
  But if you have several full duplicates in rows - edit action will edit all of them. 

Limits:

Deepcopy does not available for tables without primary keys right now.


* 
  **Primary keys** now also used to identify unique rows. Now Admin Panel don't expect only 'unique' key in model. Now it firstly works with Primary Keys and only if primary key not exist in model - use 'unique' fields to identify unique rows. Also it supports Composite Primary keys (2 and more fields) in all type of operations: delete/update/insert/deepcopy/copy.

* 
  **Schemas support**

Now if you work using the custom "schema" name - it's okay and supported by Admin Panel.  


#. **Fixed in types support**\ :


* passing data as a string - now supported both Date & DateTime format (before correct work only DataTime format)
* parsing lists (for fields with ARRAY type), also parsed type inside array


#. **Types support improvement**\ : 


* Added support for ARRAYS, TEXT, SmallInt, CHAR, Time


#. **New features**\ : 


* 
  Added Users to Admin Panel - now you can add multiple users for the panel to track history of changes correct and separate accesses

* 
  URI to DB now can be passed as config parameter 'db_uri' or with env variable 'DB_URI',
  for example, no need to setup SANIC variables:

.. code-block:: python


   create_admin_app(
           host="0.0.0.0",
           port=os.getenv("PORT", 5000),
           db=example.models.db,
           db_models=db_models,
           config={
               "presets_folder": os.path.join(current_path, "csv_to_upload"),
               "db_uri": "postgresql://local:local@localhost:5432/gino_admin"
           },
       )


#. **More fixes**\ :


* History works again

Supported features
^^^^^^^^^^^^^^^^^^


* Auth by login/pass with cookie check
* Create(Add new) item by one for the Model
* Delete all rows/per element
* Copy existed element (data table row)
* Edit existed data (table row)
* Search/sort in tables
* Deepcopy element (recursive copy all rows/objects that depend on chosen as ForeignKey)
* `Upload/export data from/to CSV <https://gino-admin.readthedocs.io/en/latest/csv_upload.html#upload-csv-files>`_
* SQL-Runner (execute SQL-queries)
* `Presets: Define order and Load to DB bunch of CSV-files <https://gino-admin.readthedocs.io/en/latest/presets.html>`_
* Init DB (Full clean up behavior: Drop tables & Recreate)
* `Composite CSV: Load multiple relative tables in one CSV-file <https://gino-admin.readthedocs.io/en/latest/csv_upload.html#composite-csv-to-upload>`_
* History logs on changes (log for admin panel actions - edit, delete, add, init_db, load presets and etc)
* Support multiple users for Admin panel (add, edit, remove users from 'Admin Users' page)
* UI Colors customizing

TODO:
^^^^^


* Add possible to add new Presets from GUI
* Select multiple rows for delete
* Copy/deepcopy multiple items
* Edit multiple items (?)
* Roles for Admin Panel users (split accessess)
* Filters in Table's columns
* Other staff on `Gino Project Dashboard <https://github.com/xnuinside/gino-admin/projects/1>`_

Run Admin Panel with Cli
------------------------

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


       gino-admin run examples/base_example/src/db.py --db postgresql://gino:gino@localhost:5432/gino -u admin:1234

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

Run Admin Panel as Standalone Sanic App
--------------------------------------~

Note: this method is a good approach if you use different frameworks as Main App

You can use Gino Admin as stand alone web app. Does not matter what Framework used for your main App.

Code example in:  examples/use_with_any_framework_in_main_app/
How to run example in: examples/use_with_any_framework_in_main_app/how_to_run_example.txt


#. In module where you define DB add 'if block'.
   We will use Fast API as main App in our example.

We have db.py where we import Gino as

.. code-block::

       from gino.ext.starlette import Gino

       db = Gino(
           dsn='postgresql://gino:gino@localhost:5432/gino'
       )

But if we use this module in Admin Panel we need to have initialisation like this:

.. code-block::

       from gino.ext.sanic import Gino
       db = Gino()

To get this, we will add some flag and based on this flag module will init db in needed to as way:

.. code-block::


       if os.environ.get('GINO_ADMIN'):
           from gino.ext.sanic import Gino
           db = Gino()
       else:
           from gino.ext.starlette import Gino
           db = Gino(dsn='postgresql://gino:gino@localhost:5432/gino')

So, if now 'db' used by Gino Admin - we use init for Sanic apps, if not - we use for our Main application Framework

Now, we need to create **admin.py** to run admin panel:

.. code-block::

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
^^^^^^^

Load multiple CSV to DB in order by one click. 
Presets described that CSV-s files and in that order need to be loaded in DB.

Read the docs: `Presets <https://gino-admin.readthedocs.io/en/latest/presets.html>`_

Composite CSV to Upload
^^^^^^^^^^^^^^^^^^^^^^^

Composite CSV - one file that contains data for several relative tables. 

Read the docs: `Composite CSV to Upload <https://gino-admin.readthedocs.io/en/latest/csv_upload.html#composite-csv-to-upload>`_

Config Gino Admin
^^^^^^^^^^^^^^^^^

Read the docs: `Config <https://gino-admin.readthedocs.io/en/latest/config.html>`_

Init DB
^^^^^^^

Init DB feature used for doing full clean up DB - it drop all tables & create them after Drop for all models in Admin Panel.

Upload from CSV
^^^^^^^^^^^^^^^

Files-samples for example project can be found here: **examples/base_example/src/csv_to_upload**

Authorization
^^^^^^^^^^^^^

Read in docs: `Authorization <https://gino-admin.readthedocs.io/en/latest/authorization.html>`_

Limitations
^^^^^^^^^^^

In current version, for correct work of Deepcopy feature in Admin Panel model MUST contain at least one unique or primary_key Column (field).

Screens:
^^^^^^^^

Check in docs: `UI Screens <https://gino-admin.readthedocs.io/en/latest/ui_screens.html>`_
