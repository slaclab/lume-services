# Demo

LUME-services is packaged with a docker-compose development spec that can be used to spin up a devlopment environment for local testing of packages.
Host port forwardings have default values, but can be modified at spin-up using a subset of the LUME-services configuration environment variables.

| Environment variable              | Default              |
|-----------------------------------|----------------------|
| LUME_MODEL_DB__USER               | root                 |
| LUME_MODEL_DB__PASSWORD           | password             |
| LUME_MODEL_DB__PORT               | 3306                 |
| LUME_PREFECT__SERVER__TAG         | core-1.2.4           |
| LUME_PREFECT__SERVER__HOST_PORT   | 4200                 |
| LUME_PREFECT__HASURA__HOST_PORT   | 3000                 |
| LUME_PREFECT__GRAPHQL__HOST_PORT  | 4201                 |
| LUME_PREFECT__POSTGRES__HOST_PORT | 5432                 |
| LUME_PREFECT__POSTGRES__DB        | prefect_db           |
| LUME_PREFECT__POSTGRES__USER      | prefect_user         |
| LUME_PREFECT__POSTGRES__PASSWORD  | prefect_password     |
| LUME_PREFECT__POSTGRES__DATA_PATH | /tmp/lume/postgresql |
| LUME_RESULTS_DB__PORT             | 27017                |
| LUME_RESULTS_DB__USERNAME         | root                 |
| LUME_RESULTS_DB__PASSWORD         | password             |


Additional variables control post-spin-up initialization of databases:

| LUME_RESULTS_DB__DATABASE | test     |


export LUME_PREFECT_BACKEND=docker



## Start services with docker-compose

Use utility packaged with lume-services to start dockerized services and to create

```
python lume_services/cli/docker.py start-docker-services
```

## Docker-compose

- Because we use bind-mounts, container persistence is
- Whenever you use docker-compose up, the container is persisted. In order to get

"down -v", "rm --stop --force"]
