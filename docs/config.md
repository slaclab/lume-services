# Configuration

LUME-services uses [injection](https://python-dependency-injector.ets-labs.org/) for runtime configuration of services. This means that programs can use the same code in a number of different environments simply by setting environment variables.

## The LUMEServicesSettings object
Applications that LUME-services tools (the MongoDB implementation of Results Database and MySQL model database), can use the configuration tools packaged with LUME-services directly by calling the configure script during code execution:
```
from lume_services.config import configure, LUMEServicesSettings
from lume_services.services.models.db import ModelDBConfig
from lume_services.services.results.mongodb import MongodbResultsDBConfig
from lume_services.services.scheduling.backends.server import (
    PrefectAgentConfig,
    PrefectConfig,
    PrefectServerConfig,
)
from lume_services import config

from lume_services.services.files.filesystems import (
    MountedFilesystem,
)

model_db_config = ModelDBConfig(
    host="127.0.0.1",
    port=3306,
    user="root",
    password="test",
    database="model_db",
)

results_db_config = MongodbResultsDBConfig(
    port=27017,
    host="127.0.0.1",
    username="root",
    database="model_db",
    password="test",
)

prefect_config = PrefectConfig(
    server=PrefectServerConfig(
        host="http://localhost", 
        host_port=4200, 
    ),
)

agent=PrefectAgentConfig(
  host="http://localhost", 
  host_port=5000,
  backend="server",
  debug=True,
)

mounted_filesystem = MountedFilesystem(
        mount_path="~/sandbox/lume-services",
        mount_alias="/User/my_user/data",
        identifier="mounted",
        mount_type="DirectoryOrCreate",
    )

settings = config.LUMEServicesSettings(
    model_db=model_db_config,
    results_db=results_db_config,
    prefect=prefect_config,
    backend="docker",
    mounted_filesystem=mounted_filesystem,
)

config.configure(settings)
```

Configurations are held on [LUMEServicesSettings](api/config#LUMEServicesSettings) objects. For more information on how configurations are handled with injection, see [`developer/configuration`](developer/configuration.md).

## Configure from environment
The LUME-services environment may alternatively be configured using environment variables by calling the configure method without an argument.

```python
from lume_services.config import configure

configure()
```

Relevant environment variables (these tables are built using script in `scripts/build_configuration_table.py` automatically generated w/ the GitHub build action defined in `.github/workflows/build_docs.yml`, see **note beneath):

{% include 'files/env_vars.md' %}

**note: I haven't validated these table. Sorry! You can check the  fields directly [here](). 





##  Custom configuration

The `lume-services.config.configure` method provides tooling for one specific architecture configuration, but other users may want to use different database implementations (see [services](developer/services)). These applications can define their own methods using the same interface by subclassing the base class of artifacts that is injected into each service:


base class -> service injected into:


* `lume_services.services.files.filesystems.filesystem` -> `lume_services.services.files.service`
* `lume_services.services.results.db` -> `lume_services.services.results.service`
* `lume_services.services.models.db.db` -> `lume_services.services.models.services`
* `lume_services.services.scheduling.backends.backend` -> `lume_services.services.scheduling.service`
* (Downstream, for things like slurm scheduling) `lume_services.hpc.provider` -> `lume_services.services.hpc.service`

