#### Contributions

Contributions are very welcome!


If you have time and want to contribute - take any open issue or open if you have a bug or need a new feature.

You can also contact me in telegram: @xnuinside or mail: xnuinside@gmail.com if have any questions or suggestions


#### Install pre-commit hooks

Project use pre-commit hooks, so you need setup them

Just run:

.. code-block:: python

    pre-commit install

to install git hooks in your .git/ directory.

#### How to run integration tests


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

