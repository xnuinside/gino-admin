UI Customization
========================

Change UI Colors
------------------

.. image:: ../img/incremental_ids_support.png
  :alt: Incremental Fields


Config object has section 'ui'. In UI section now exist 'colors' where you can set up colors that will be used for:

- Primary buttons. Property: buttons
- Second buttons. Property: buttons_second
- Alert buttons (actions that something remove/reset - deleted, drop db and etc). Property: buttons_alert
- Tables headers. Property: table
- Tables with Alert headers (like in Init DB). Property: table_alerts
- Footer background. Property: footer
- Header background. Property: header

Admin panel used Semantic UI as CSS Framework so all names of possible colors is described and showed here:
https://semantic-ui.com/usage/theming.html 

(red: #B03060; orange #FE9A76; yellow: #FFD700; olive:  #32CD32 green:  #016936; teal :  #008080; blue :  #0E6EB8; violet: #EE82EE; purple: #B413EC; pink:  #FF1493; brown:  #A52A2A; grey :  #A0A0A0; black:  #000000;)


To change colors pass config as:

.. code-block::python

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


Set Custom Header
------------------

To do this just set provide config argument:
 
      - name: project name, that will be displayed in UI. By default it shows: "Sanic-Gino Admin Panel"

Example:

.. code-block:: python

    if __name__ == "__main__":
    create_admin_app(
        db.db,
        create_models_list(db),
        port=os.environ.get("PORT", "5000"),
        config={
            "name": "Colored UI"
            }

Example in github: https://github.com/xnuinside/gino-admin/blob/master/examples/colored_ui/src/app.py#L28 

