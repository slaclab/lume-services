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


## GitHub actions build
Upon push of a tag to the repository, the GitHub action defined in `.github/workflows/build_sdist.yml` will publish the [source distribution](https://docs.python.org/3/distutils/sourcedist.html) to the GitHub release artifact. Users installing LUME-services using pip should point to the sdist file.



The environment resolver uses the sdist info in order to register
See more notes [here](services/models.md#environment-resolution).


This workflow requires the GitHub secret: GITHUB_TOKEN to be set for the repository. This can be confiured by creating an [access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) and setting it on the repo using the GitHub interface.
