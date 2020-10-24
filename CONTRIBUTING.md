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


Run integrations test from  tests/integration_tests/tests:

```
    cd test/integration_tests/docker
```

1. Prepare docker-compose for tests:

```bash

    ./run.sh docker-compose up --build

```
Command will build all necessary images & run docker compose cluster.

2. Run tests

```bash

    pytest ../tests --docker-compose=docker-compose.yml --docker-compose-no-build --use-running-containers -vv

```