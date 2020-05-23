Presets
=======

Presets allow you to load multiple CSV to DB in order by one click.

For this you need to define folder with DB presets. Inside folder you puy config files for Presets described in yml format.
In config file you define order in what to load CSV-s files, that files used to populate tables.

To see more clear example check & run examples with CSV in `examples/base_example folder`_.

.. _examples/base_example folder: https://github.com/xnuinside/gino-admin/tree/master/examples/base_example

Let's take a look on preset sample:

.. code-block:: python

    id: first_preset
    name: First Preset
    description: "Init DB with minimal data"
    files:
      users: csv/user.csv
      gifts: csv/gift.csv

This mean preset contains 2 csv files, firstly will  be loaded csv/user.csv to users table, second will be loaded csv/gift.csv to gifts table.

In order defined in yml, Gino-Admin will load csv files to models.
'files:' describe that file (right sight) must be loaded to the model (left side).

Don't forget to setup path to folder with presets like with **'presets_folder'** argument, by default it tries to find presets in 'presets/' folder.

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

Check code samples in `examples/base_example/`_

.. _examples/base_example/: https://github.com/xnuinside/gino-admin/blob/master/examples/base_example/src/app.py#L40
