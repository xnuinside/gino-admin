## Gino-Admin

![Gino-Admin Logo](docs/img/logo/g_logo.svg) 

Docs (state: in process): [Gino-Admin docs](https://gino-admin.readthedocs.io/en/latest/ui_screens.html)

Play with Demo (current master 0.0.11a2) [>>>> Gino-Admin demo <<<<](http://www.xnu-im.space/gino_admin_demo/login)


![badge1](https://img.shields.io/pypi/v/gino_admin) ![badge2](https://img.shields.io/pypi/l/gino_admin) ![badge3](https://img.shields.io/pypi/pyversions/gino_admin) 


Admin Panel for PostgreSQL DB with Gino ORM and Sanic

![Table view](docs/img/table_view_new.png)
![Load Presets](docs/img/db_presets.png)


### Supported features

- Auth by login/pass with cookie check
- Create(Add new) item by one for the Model
- Search/sort in tables
- [Upload/export data from/to CSV](https://gino-admin.readthedocs.io/en/latest/csv_upload.html#upload-csv-files)
- Delete all rows/per element
- Copy existed element (data table row)
- Edit existed data (table row)
- SQL-Runner (execute SQL-queries)
- [Presets: Define order and Load to DB bunch of CSV-files](https://gino-admin.readthedocs.io/en/latest/presets.html)
- Drop DB (Full clean up behavior: Drop tables & Recreate)
- Deepcopy element (recursive copy all rows/objects that depend on chosen as ForeignKey)
- [Composite CSV: Load multiple relative tables in one CSV-file](https://gino-admin.readthedocs.io/en/latest/csv_upload.html#composite-csv-to-upload)


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
    
    pip install gino-admin==0.0.11
    

### Updates
#### Version 0.0.11:
1. Added possibility to define custom route to Gino Admin Panel. With 'route=' config setting
By default, used '/admin' route

2. Added Demo Panel  [Gino-Admin demo](http://xnu-in.space/gino_admin_demo) - you can log in and play with it. Login & pass - admin / 1234
If you don't see any data in UI maybe somebody before you cleaned it - go to Presets and load one of the data presets.

3. Fixed minors issues: 
1) floats now displayed with fixed number of symbols. Parameter can be changed with config param `round_number=`.
2) now file upload fill not raise error if no file was chosen 
3) fixed issue with session & auth key

4. Deepcopy now ask id - you can use auto-generated or define own id to 'deepcopy object'

![Table view](docs/img/deepcopy.png)

Full changelog for all versions see in [CHANGELOG.txt](CHANGELOG.txt)

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


### Presets

Load multiple CSV to DB in order by one click. 
Presets described that CSV-s files and in that order need to be loaded in DB.

Read the docs: [Presets](https://gino-admin.readthedocs.io/en/latest/presets.html)


### Composite CSV to Upload

Composite CSV - one file that contains data for several relative tables. 

Read the docs: [Composite CSV to Upload](https://gino-admin.readthedocs.io/en/latest/csv_upload.html#composite-csv-to-upload)


### Config Gino Admin

Read the docs: [Config](https://gino-admin.readthedocs.io/en/latest/config.html)



### Drop DB (Init DB)

Drop DB feature used for doing full clean up DB - it drop all tables & create them after Drop for all models in Admin Panel.



### Upload from CSV

Files-samples for example project can be found here: **examples/base_example/src/csv_to_upload**


### Authorization

Read in docs: [Authorization](https://gino-admin.readthedocs.io/en/latest/authorization.html)


### Limitations


For correct work of Admin Panel all models MUST contain at least one unique and primary_key Column (field).

This column used to identify row (one element) for Copy & Edit & Delete operations.
Name of unique and primary_key column and type does not matter.

So if you define model, for example, User, you can have column **user_id** as unique and primary_key:

```
    class User(db.Model):

        __tablename__ = "users"

        user_id = db.Column(db.String(), unique=True, primary_key=True)
```

Or for model 'Country' it can be 'code'

```
    class Country(db.Model):

        __tablename__ = "countries"

        code = db.Column(db.String(8), unique=True, primary_key=True)
        name = db.Column(db.String())
```

### Screens:

Check in docs: [UI Screens](https://gino-admin.readthedocs.io/en/latest/ui_screens.html)

