.. gino-admin documentation master file, created by
   sphinx-quickstart on Sat May 23 20:17:41 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Gino-Admin's documentation!
======================================

Docs status: work in progress

Project's github: https://github.com/xnuinside/gino-admin



|badge1| |badge3| |badge2|

.. |badge1| image:: https://img.shields.io/pypi/v/gino_admin
.. |badge2| image:: https://img.shields.io/pypi/l/gino_admin
.. |badge3| image:: https://img.shields.io/pypi/pyversions/gino_admin


Admin Panel for PostgreSQL DB with Gino ORM and Sanic

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/table_view_new.png
  :width: 250
  :alt: Table view

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/db_presets.png
  :width: 250
  :alt: Load Presets

Installation
------------

.. code-block:: console

    $ pip install gino-admin==0.0.10


Quick start
-----------

Check in :doc:`quick_start.rst`


Version 0.0.10 Updates:
-----------------------
1. GinoAdmin Config moved to Pydantic.
Added possible to send any properties to config with config dict. Example:
.. code-block:: python

    add_admin_panel(
        app,
        db,
        [User, Place, City, GiftCard, Country, Item],
        # any Gino Admin Config params you can pass as named params
        custom_hash_method=custom_hash_method,
        presets_folder=os.path.join(current_path, "csv_to_upload"),
        name='Base Example')


2. Added Config param 'name' - this is a name, that will be showed in header near menu.
By Default it is display "Sanic-Gino Admin Panel", now you can change it to your header.

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/custom_header.png

3. UI updates: Gino Admin Panel version now showed in UI footer, Login page now more presentable,
changed index page of Admin Panel, now it presented main feature.

.. image:: https://github.com/xnuinside/gino_admin/blob/master/docs/img/custom_header.png

4. Initialised first project's docs

5. Edit/Delete now take object's unique key as argument and stop fall if in key was '/' symbol

6. Added param 'csv_update_existed' in Config. By default 'csv_update_existed = True'. This mean if you upload CSV with rows with unique keys, that already exist in DB - it will update all fields with values from CSV.
You can turn off it with set 'csv_update_existed = False'.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quick_start
   cli
   examples
   config
   features
   rest_api
   presets
   csv_upload
   changelog
   ui_screens

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
