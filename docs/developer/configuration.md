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

container provides runtime context


Once configured, the injection container will provide the configured services to LUME-services objects. For example, the signature for _ looks like _:

...

This means that _ can be run using manual instantiation, or by using injection by precipating the code with:

```
from lume_services.config import configure

configure()
...

```

Applications can take advantage of this feature by... WIRING...



# Pydantic

# Pydantic docker secrets:
https://pydantic-docs.helpmanual.io/usage/settings/
Secret strings used for passwords
