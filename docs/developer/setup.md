# Setup developer tools

First, create the development environment with conda.
```
conda env create -f dev-environment.yml
conda activate lume-services-dev
```
The repository is packaged using pre-commit hooks for code format consistency. In order to install, run:
```
pre-commit install
```


## Requirements management

Requirements are tracked in a number of places and must be kept in sync.
In the repository root we have:
 - `requirements.txt`: Run requirements for the package.
 - `dev-requirements.txt`: Requirements for development. Includes packages for testing and formatting hooks.
 - `docs-requirements.txt`: Requirements for building package documentation.
 - `dev-environment.yml`: Developer environment, which should be kept in sync with the above.

There is an additional `environment.yml` packaged in `lume_services.docker.files` which must be consistent with requirements defined in the repository root. This file is used for composing the Docker image inside which workflows will run in a distributed configuration. This file is also used for [isolated environment resolution](docker_image.md#isolation).
