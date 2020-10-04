Configure Gino Admin
====================

You can define in config:

* presets_folder: path where stored predefined DB presets
* custom_hash_method: method that used to hash passwords and other data, that stored as '_hash' columns in DB, by default used pbkdf2_sha256.encrypt
* composite_csv_settings: describe some rules how to parse and load Composite CSV files
* name: project name, that will be displayed in UI. By default it shows: "Sanic-Gino Admin Panel"
* csv_update_existed: By default 'csv_update_existed = True'. This mean if you upload CSV with rows with unique keys, that already exist in DB - it will update all fields with values from CSV. You can turn off it with set 'csv_update_existed = False'.
* route: Route where will be served (that will be used to access) Admin panel. By default, used '/admin' route
* round_number: How much symbols display in floats in UI (default 3)
* db_uri: pass path & credentials to DB with db_uri, example: "postgresql://local:local@localhost:5432/gino_admin"

composite_csv_settings
######################

composite_csv_settings allow to define multiple tables as one alias

For example, in our example project with composite CSV we have 3 huge different categories separated by tables (they have some different columns) - Camps, Education(courses, lessons, colleges and etc.) and Places(Shopping, Restaurants and etc.)
But we want to avoid duplicate similar columns 3 times, so we can call those 3 tables by one alias name,
for example: 'area' and some column to understand that exactly this is an 'area' - capms, educations or places table for this we need to define 'type_column' we don't use in any model column 'type' so we will use this name for type-column

So, now let's define **composite_csv_settings**

.. code-block:: python

    composite_csv_settings={
        "area": {"models": (Place, Education, Camp), "type_column": "type"}
    }

This mean, when we see in CSV-header 'area' this is data for one of this 3 models, to identify which of this 3 models - check column with header 'area:type'.
In type column values must be same 1-to-1 as table names.

Check source code with example: examples/composite_csv_example

And table sample for it: https://docs.google.com/spreadsheets/d/1ur63acwWExyjWouZ1WEkUxCX73vOcdXzCrEYc7cPhTg/edit?usp=sharing

You also can define table name as 'pattern':

.. code-block:: python

    composite_csv_settings={
        "area": {"models": (SomeModel, SomeModel2, SomeModel3), "pattern": "*_postfix"}
    }

This mean - to understand that this is a DB - take previous table from CSV in row and add '_postfix' at the end.
