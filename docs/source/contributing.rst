Contributing
============

Contributions and feature requests are very welcome!


If you have time and want to fix:
Please open issues with that you want to add
or write to me in Telegram: @xnuinside or mail: xnuinside@gmail.com


Developer guide
---------------

Project use pre-commit hooks, so you need setup them

Just run:

.. code-block:: python

    pre-commit install

to install git hooks in your .git/ directory.


How to run integration tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Run integrations test from  tests/integration_tests/

.. code-block:: console

cd test/integration_tests

When 2 possible ways.

First way.

.. code-block:: console

    pytest . --docker-compose=test-docker-compose.yml -v

    # will build and run docker compose & execute the tests


Second way (reduce time in process of tests creating/debuggind)

.. code-block:: console

    docker-compose -f test-docker-compose.yml up --build

    # build & run test cluster

    # when in new terminal window:

    pytest . --docker-compose=test-docker-compose.yml --docker-compose-no-build --use-running-containers -v
