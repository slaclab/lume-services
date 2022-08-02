# TODO:
## Repo setup
- TODO:
    - [ ] Docs for injection and container
    - [ ] Move any services in __init__ files to a service.py
    - [ ] Remove tests in pip installation, move to directory base
    - [ ] Docs!
    - [ ] Set up all loggers
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

## Template
TODO:
    - [ ] CLI tool
    - [ ] Instructions for templating tool and configuration
    - [ ] Templated README
    - [ ] Handling of input/output variables at outset
    - [ ] Drop required defaults for lume-model variables
    - [ ] Check functionality of all
    - [ ] Docs
- Done:
    - [x] Action for testing package install & running pytests
    - [x] Upload docker image to repo artifacts 5/3
    - [x] Docker build action for templated repos 4/12

## Databases
- TODO:
    - [ ] Test database failure cases
    - [x] Rename base classes for DBService
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

## Backlog
- TODO:
    - [ ] Implement/plan for logging infrastructure
    - [ ] Synchronous snapshot service (-> SLAC-services)
    - [ ] HPC interface
    - [ ] Slurm interface
    - [ ] Output service (-> LUME-EPICS?)
- Done:
    - [x] Finish util testing

## Scheduler
- TODO:
    - [ ] Test flow of flows composition
    - [ ] Add mapped parameters to database?
    - [ ] Kubernetes backend tests
    - [ ] Docs
    - [ ] Drop all but apollo from config
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

## Misc
- TODO:
    - [ ] Separate template into own repo and use git submodule
    - [ ] Could abstract docker compose versions
- Done:
    - [x] Rename file.systems to file.filesystems and all files names service.py
    - [x] Move fixtures from conftest to designated files under tests/fixtures
    - [x] Change LUME-model SurrogateModel to BaseModel for generalizability

## Files
- TODO:
    - [ ] File locks
- Done:
    - [x] Implement local file handler 5/2
    - [x] Implement mounted filesystem handler 5/2

## Models
- TODO:
    - [ ] Create model interface with injected services
    - [ ] Add utility for loading flow objects
    - [ ] Preprocessing tasks?

- Done:



## Modeling
- TODO:
    - [ ] Preprocessing structure
    - [ ] Registration of preprocessing flows
