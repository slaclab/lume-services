# TODO:

## In progress
### Repo setup
- [ ] Action for testing package install & running pytests
- [ ] Action for building docs

### Template
- [ ] Add versioneer config. Versioneer install needs to happen on init.
- [ ] CLI tool
- [ ] Documentation of tool and configuration

### Databases
- [ ] Add uniqueness constraints on the model table 
- [ ] MySQL schema unique key constraints
- [ ] Test database failure cases 
- [ ] Transition from pytest-mysql to remove pip dependency

## Backlog
- [ ] Implement/plan for logging infrastructure

## Maybe TODO
- [ ] Automatically generate diagram from .sql schema?

## Done:
- [x] Initial tests for mysql model db
- [x] Abstraction of database schema and auth config from query execution
- [x] Add flow_to_deployments into db 
- [x] flow_to_deployments table +
- [x] Change model_versions to deployments in schema
- [x] Versioneer
- [x] Make mongodb multiprocessing safe
- [x] Add uniqueness to results
