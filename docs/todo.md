# TODO:

## In progress
### Repo setup
- [ ] Action for testing package install & running pytests
- [ ] Docs for injection and container
- [x] Tests for injection and container 7/5
- [x] Environment variables with extensible prefix 7/5
- [ ] Move any services in __init__ files to a service.py

### Template
- [ ] CLI tool
- [ ] Instructions for templating tool and configuration
- [ ] Templated README
- [x] Action for testing package install & running pytests
- [x] Upload docker image to repo artifacts 5/3
- [ ] Handling of input/output variables at outset
- [ ] Drop required defaults for lume-model variables
- [ ] Check functionality of above

### Databases
- [ ] Test database failure cases
- [ ] Rename base classes for DBService

## Backlog
- [ ] Implement/plan for logging infrastructure
- [ ] Synchronous snapshot service (-> SLAC-services)
- [ ] HPC interface
- [ ] Output service (-> LUME-EPICS?)
- [x] Finish util testing

## Scheduler
- [ ] Refactor scheduler
- [ ] Flow of flows composition
- [x] Create prefect flow image 6/26
- [x] Remove redundant flow storage during build in pytest 7/6

## Maybe TODO
- [ ] Separate template into own repo?
- [ ] Rename model service to model registry service
- [x] Rename file.systems to file.filesystems and all files names service.py
- [x] Move fixtures from conftest to designated files under tests/fixtures
- [ ] Could abstract docker compose versions

## Other
- [ ] Dashboard image field in mongodb for impact
- [ ] Constrain KubernetesBackend image pull policy to existing options

## Files
- [ ] File locks
- [ ] Change Filesystem to FilesystemHandler

## Modeling
- [ ] Preprocessing structure
- [ ] Registration of preprocessing flows

## Done:
- [x] Initial tests for mysql model db
- [x] Abstraction of database schema and auth config from query execution
- [x] Add flow_to_deployments into db
- [x] flow_to_deployments table +
- [x] Change model_versions to deployments in schema
- [x] Versioneer
- [x] Make mongodb multiprocessing safe
- [x] Add uniqueness to results
- [x] Docker build action for templated repos 4/12
- [x] Change LUME-model SurrogateModel to BaseModel for generalizability
- [x] Fix test connection with mysql in-package plugin. "Connection refused" 4/13
- [x] License should be passed or something generic. SLAC license shouldn't be in LUME 4/12
- [x] Add versioneer config. Versioneer install needs to happen on init. 4/12
- [x] DB result using documents 4/14
- [x] Transition from pytest-mysql to remove pip dependency 4/15
- [x] Basics of injection and container 4/15
- [x] File result 5/2
- [x] Implement local file handler 5/2
- [x] Implement mounted filesystem handler 5/2
- [x] Action for building docs
- [x] Automatically generate diagram from .sql schema? 5/6
- [x] MySQL schema unique key constraints 5/12
- Scheduling
    - [x] Drop prefect subfolder 6/24
    - [x] Create docker backend 6/27
    - [x] Tesing infrastructure for prefect w/ docker compose 6/27
