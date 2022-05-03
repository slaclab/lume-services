# TODO:

## In progress
### Repo setup
- [ ] Action for testing package install & running pytests
- [ ] Action for building docs
- [ ] Docs for injection and container
- [ ] Tests for injection and container
- [ ] Environment variables with extensible prefix

### Template
- [ ] CLI tool
- [ ] Instructions for templating tool and configuration
- [ ] Templated README
- [ ] Action for testing package install & running pytests
- [ ] Add upload of docker image to repo artifacts as well
- [ ] Handling of input/output variables at outset
- [ ] Drop required defaults for lume-model variables

### Databases
- [ ] Add uniqueness constraints on the model table 
- [ ] MySQL schema unique key constraints
- [ ] Test database failure cases 

## Backlog
- [ ] Implement/plan for logging infrastructure
- [ ] Synchronous snapshot service
- [ ] Update scheduler
- [ ] Modeling service

## Maybe TODO
- [ ] Automatically generate diagram from .sql schema?
- [ ] Separate template into own repo?

## Other
- [ ] Dashboard image field in mongodb for impact

## Files
- [ ] Implement mounted file handler
- [ ] File locks

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
- [x] Fix test connection with in-package plugin. "Connection refused" 4/13
- [x] License should be passed or something generic. SLAC license shouldn't be in LUME 4/12
- [x] Add versioneer config. Versioneer install needs to happen on init. 4/12
- [x] DB result using documents 4/14
- [x] Transition from pytest-mysql to remove pip dependency 4/15
- [x] Basics of injection and container 4/15
- [x] File result 5/2
- [x] Implement local file handler 5/2