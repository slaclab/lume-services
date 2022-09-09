# Configuration

LUME-services is entirely configurable by environment variables. The environment variables are collected from a [pydantic BaseSettings](https://pydantic-docs.helpmanual.io/usage/settings/) object, [`LUMEServicesSettings`](../api/config.md#LUMEServicesSettings), in `lume_services.config`.


This object gathers all configurations used by LUME-services and exposes them through a single interface.




Command line tools call the configuration here:

So on any attempts to run a command line tool, the LUMEServicesSettings are inferred from the environment variables.


In `LUMEServicesSettings.Config` we set the options for constructing the environment variable:
```python
class LUMEServicesSettings(BaseSettings):
    """Settings describing configuration for default LUME-services provider objects."""

    model_db: Optional[ModelDBConfig]
    results_db: Optional[MongodbResultsDBConfig]
    prefect: Optional[PrefectConfig]
    mounted_filesystem: Optional[MountedFilesystem]
    backend: str = "local"
    # something wrong with pydantic literal parsing?
    # Literal["kubernetes", "local", "docker"] = "local"

    class Config:
        # env_file = '.env'
        # env_file_encoding = 'utf-8'
        validate_assignment = True
        env_prefix = "LUME_"
        env_nested_delimiter = "__"

```
This means that out environment variables will be prefixed with "LUME_" and sub-configurations will be prefixed by "__", following the first level configuration options. These variables are not case sentsitive. So, to set the host_port of the model database configuration, we can use the environment variable `LUME_MODEL_DB__PORT` and to set the host port for the prefect server we use `LUME_PREFECT__SERVER__HOST_PORT`.


## Injection

LUME-services uses dependency injection for service management. High level APIs use abstracted service APIs instead of the services themselves. This design facilitates portable code with services configurable at runtime by environment variables. Abstracted base classes provide functional patterns for implementing custom services compatable with LUME-services code.

The service APIs and their respective injected base classes are listed below:


| Service API | Injected Service Base Class |
|-------------|-----------------------------|
|             |                             |
|             |                             |
|             |                             |

The base classes provide 

The injected services are used to initialize the service API during runtime with 


 by constructing a Python [dependency_injector `DeclarativeContainer`](https://python-dependency-injector.ets-labs.org/) in `lume_services.config`. This container is referenced 



Using classes other than the defaults requres implementation of a custom `configure` method...



 For example:

```

```


The container provides 

Once configured, the injection container will provide the configured services to LUME-services objects. For example, the signature for _ looks like _:

...

This means that _ can be run using manual instantiation, or by using injection by precipating the code with:

```
from lume_services.config import configure

configure()
...

```

Applications can take advantage of this feature by... WIRING...

## Propogation of environment to jobs

In order for deployed jobs to appropriately configure access to services (results database, filesystems, etc.), appropriate environment variables must be propogated to the jobs. [Prefect Agents](https://docs-v1.prefect.io/orchestration/agents/overview.html) are responsible for starting and monitoring the results of flows.

Agent in docker-compose is started with env flags- passes these env vars to all jobs kicked off
In the `docker-compose.yml` packaged in `lume_services.docker.files`:

```yaml
  agent:
    image: prefecthq/prefect:1.2.3-python3.10
    command: >
      bash -c "prefect server create-tenant --name default --slug default &>/dev/null ;
      prefect agent docker start --label lume-services --agent-address http://localhost:5000/ --show-flow-logs --log-level DEBUG --network service-net  --env LUME_BACKEND=$LUME_BACKEND --env LUME_MOUNTED_FILESYSTEM__IDENTIFIER=$LUME_MOUNTED_FILESYSTEM__IDENTIFIER --env LUME_MOUNTED_FILESYSTEM__MOUNT_PATH=$LUME_MOUNTED_FILESYSTEM__MOUNT_PATH --env LUME_MOUNTED_FILESYSTEM__MOUNT_ALIAS=$LUME_MOUNTED_FILESYSTEM__MOUNT_ALIAS --env LUME_MOUNTED_FILESYSTEM__MOUNT_TYPE=$LUME_MOUNTED_FILESYSTEM__MOUNT_TYPE --env LUME_ENVIRONMENT__LOCAL_PIP_REPOSITORY=$LUME_ENVIRONMENT__LOCAL_PIP_REPOSITORY --env LUME_ENVIRONMENT__LOCAL_CONDA_CHANNEL_DIRECTORY=$LUME_ENVIRONMENT__LOCAL_CONDA_CHANNEL_DIRECTORY --env LUME_MODEL_DB__HOST=$LUME_MODEL_DB__HOST --env LUME_MODEL_DB__PORT=$LUME_MODEL_DB__PORT --env LUME_MODEL_DB__USER=$LUME_MODEL_DB__USER --env LUME_MODEL_DB__PASSWORD=$LUME_MODEL_DB__PASSWORD --env LUME_RESULTS_DB__USERNAME=$LUME_RESULTS_DB__USERNAME --env LUME_RESULTS_DB__PASSWORD=$LUME_RESULTS_DB__PASSWORD --env LUME_RESULTS_DB__PORT=$LUME_RESULTS_DB__PORT:-27017 --env LUME_RESULTS_DB__HOST=$LUME_RESULTS_DB__HOST --env  LUME_PREFECT__SERVER__HOST=$LUME_PREFECT__SERVER__HOST --env  LUME_PREFECT__SERVER__HOST_PORT=$LUME_PREFECT__SERVER__HOST_PORT --env  LUME_PREFECT__HOME_DIR=$LUME_PREFECT__HOME_DIR --env LUME_PREFECT__DEBUG=$LUME_PREFECT__DEBUG --env LUME_PREFECT__BACKEND=$LUME_PREFECT__BACKEND"
    environment:
      PREFECT__LOGGING__LEVEL: DEBUG
      LUME_MODEL_DB_PORT:
      LUME_MOUNTED_FILESYSTEM__IDENTIFIER: mounted
      LUME_MOUNTED_FILESYSTEM__MOUNT_PATH: ${PWD}
      LUME_MOUNTED_FILESYSTEM__MOUNT_ALIAS: /working_directory
      LUME_MOUNTED_FILESYSTEM__MOUNT_TYPE: DirectoryOrCreate
      LOCAL_CHANNEL_ONLY: ${LUME_PREFECT__ISOLATED:-False}
      LUME_ENVIRONMENT__LOCAL_PIP_REPOSITORY: ${LUME_EVIRONMENT__LOCAL_PIP_REPOSITORY}
      LUME_ENVIRONMENT__LOCAL_CONDA_CHANNEL_DIRECTORY: ${LUME_EVIRONMENT__LOCAL_CONDA_CHANNEL_DIRECTORY}
      LUME_MODEL_DB__HOST: http://mysql
      LUME_MODEL_DB__PORT: ${LUME_MODEL_DB__PORT:-3306}
      LUME_MODEL_DB__USER: ${LUME_MODEL_DB__USER:-root}
      LUME_MODEL_DB__PASSWORD: ${LUME_MODEL_DB__PASSWORD:-password}
      LUME_MODEL_DB__DATABASE: ${LUME_MODEL_DB__DATABASE:-lume_services_models}
      LUME_RESULTS_DB__DATABASE: ${LUME_MODEL_DB__DATABASE:-results}
      LUME_RESULTS_DB__USERNAME : ${LUME_RESULTS_DB__USERNAME:-root}
      LUME_RESULTS_DB__HOST: http://mongodb
      LUME_RESULTS_DB__PASSWORD: ${LUME_RESULTS_DB__PASSWORD:-password}
      LUME_RESULTS_DB__PORT: 27017
      LUME_PREFECT__SERVER__HOST: apollo
      LUME_PREFECT__SERVER__HOST_PORT: 42001
      LUME_PREFECT__HOME_DIR: ~/.prefect
      LUME_PREFECT__DEBUG: ${LUME_PREFECT__DEBUG:-false}
      LUME_PREFECT__BACKEND: server
```
The command references the assigned environment variables on the agent. In order to be compatible with LUME-services tooling, all agents must be launched using this environment variable propogation. 


# Pydantic

# Pydantic docker secrets:
https://pydantic-docs.helpmanual.io/usage/settings/
Secret strings used for passwords
