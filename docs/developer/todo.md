# TODO:
## Repo setup
- TODO:
    - [ ] Persist volumes for databases
    - [ ] Docs for injection and container
    - [ ] Docs!
    - [ ] Set up all loggers
    - [ ] Move environments, flows, tasks, and results under model directory
    - [ ] Add tests for templated repo
    - [ ] Fix docker cred handling in workflows
    - [ ] Set up with conda
    - [ ] Could test the templated flows directly with the services by using the lume-services pytest fixtures 
- Done:
    - [x] Versioneer
    - [x] Action for testing package install & running pytests
    - [x] Tests for injection and container 7/5
    - [x] Environment variables with extensible prefix 7/5
    - [x] License should be passed or something generic. SLAC license shouldn't be in LUME 4/12
    - [x] Add versioneer config. Versioneer install needs to happen on init. 4/12
    - [x] Transition from pytest-mysql to remove pip dependency 4/15
    - [x] Basics of injection and container 4/15
    - [x] Action for building docs
    - [x] Automatically generate diagram from .sql schema? 5/6s
    - [x] Move any services in __init__ files to a service.py
    - [x] Fix prefect context bug during pytest
    - [x] Fix image issue... Build a designated image in deployment using a lume-services base image
    - [x] Remove tests in pip installation


## CLI
- TODO:
    - [ ] Integrate template with LUME-services CLI tooling. Once the template is tracked as a git submodule, a command can be implemented for creating the template directly using the lume-services [entrypoint](https://github.com/slaclab/lume-services/blob/c567fd4a2f4bdd274453190a38cb804e11a25bdc/setup.py#L24).
    - [ ] Implement CLI tools for registering model deployments. At present, you need to call the in-code API as demonstrated in 
    - [ ] Add CLI tool for listing available models and deployments



## Template
- TODO:
    - [ ] Use git submodule to track template with version
    - [ ] Use relative path for cookiecutter generation
- Done:
    - [x] Action for testing package install & running pytests
    - [x] Upload docker image to repo artifacts 5/3
    - [x] Docker build action for templated repos 4/12
    - [x] Instructions for templating tool and configuration
    - [x] Templated README
    - [x] Handling of input/output variables at outset
    - [x] Raise not implemented for to-be-replaced template functions

## Databases
- TODO:
    - [ ] Test database failure cases
    - [ ] Dashboard image field in mongodb for impact
    - [ ] Docs
- Done:
    - [x] Initial tests for mysql model db
    - [x] Abstraction of database schema and auth config from query execution
    - [x] Add flow_to_deployments into db
    - [x] Change model_versions to deployments in schema
    - [x] Make mongodb multiprocessing safe
    - [x] Add uniqueness to results
    - [x] Fix test connection with mysql in-package plugin. "Connection refused" 4/13
    - [x] Rename base classes for DBService

## Backlog
- TODO:
    - [ ] Synchronous snapshot service (-> SLAC-services)
    - [ ] HPC interface
    - [ ] Slurm interface (Can we just mount the binary?)
    - [ ] Output service (this probably belongs in LUME-EPICS)
- Done:
    - [x] Finish util testing

## Scheduler
- TODO:
    - [ ] Kubernetes backend tests
    - [ ] Docs
    - [ ] Authentication for private repositories

- Done:
    - [x] Refactor scheduler 7/13
    - [x] Create prefect flow image 6/26
    - [x] Remove redundant flow storage during build in pytest 7/6
    - [x] Pin docker-py version 7/15
    - [x] Constrain KubernetesBackend image pull policy to existing options
    - [x] Drop prefect subfolder 6/24
    - [x] Create docker backend 6/27
    - [x] Tesing infrastructure for prefect w/ docker compose 6/27
    - [x] Result tasks
    - [x] Add scheduler to context
    - [x] Drop all but apollo from config 8/3
    - [x] Improve service wait_until_responsive checks and move into docker 8/9
    - [x] Test flow of flows composition
    - [x] Add requirements table
    - [x] Environment solving for containerized jobs
    - [x] Interace to model
    - [x] How do we handle submission of environment variables to the scheduler? For example, how do we communicate the aliasing of services in a docker-compose app?


## Misc
- TODO:
    - [ ] Use environment variable fixture in tests instead of modifying env
- Done:
    - [x] Rename file.systems to file.filesystems and all files names service.py
    - [x] Move fixtures from conftest to designated files under tests/fixtures
    - [x] Change LUME-model SurrogateModel to BaseModel for generalizability

## Files
- TODO:
    - [ ] Do we need file locks for the file handlers?
- Done:
    - [x] Implement local file handler 5/2
    - [x] Implement mounted filesystem handler 5/2

## Models
- TODO:
    - [x] Create model interface with injected services
    - [x] Add utility for loading flow objects
