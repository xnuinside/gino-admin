#### Contributions

Contributions are very welcome!


If you have time and want to contribute - take any open issue or open if you have a bug or need a new feature.

You can also contact me in telegram: @xnuinside or mail: xnuinside@gmail.com if have any questions or suggestions


#### Install pre-commit hooks

Project use pre-commit hooks, so you need setup them

Just run:

```
    pre-commit install
```
to install git hooks in your .git/ directory.

#### How to run integration tests


Run integrations test from  tests/integration_tests/

```
    cd test/integration_tests
```

When 2 possible ways.

First way.

```
    pytest . --docker-compose=test-docker-compose.yml -v

    # will build and run docker compose & execute the tests
```

Second way (reduce time in process of tests creating/debuggind)

```
    docker-compose -f test-docker-compose.yml up --build

    # build & run test cluster

    # when in new terminal window:

    pytest . --docker-compose=test-docker-compose.yml --docker-compose-no-build --use-running-containers -v
```