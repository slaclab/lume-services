# Base Configuration
|    Name    | Type |Default|
|------------|------|-------|
|LUME_BACKEND|string|local  |


# Filesystem Configuration
|                Name                | Type |     Default     |
|------------------------------------|------|-----------------|
|LUME_MOUNTED_FILESYSTEM__IDENTIFIER |string|mounted          |
|LUME_MOUNTED_FILESYSTEM__MOUNT_PATH |string|                 |
|LUME_MOUNTED_FILESYSTEM__MOUNT_ALIAS|string|                 |
|LUME_MOUNTED_FILESYSTEM__MOUNT_TYPE |string|DirectoryOrCreate|


# Environment Resolution
|                     Name                      | Type  |                                         Default                                          |
|-----------------------------------------------|-------|------------------------------------------------------------------------------------------|
|LUME_ENVIRONMENT__LOCAL_PIP_REPOSITORY         |string |                                                                                          |
|LUME_ENVIRONMENT__LOCAL_CONDA_CHANNEL_DIRECTORY|string |                                                                                          |
|LUME_ENVIRONMENT__BASE_ENV_FILEPATH            |string |/Users/jacquelinegarrahan/sandbox/lume-services/lume_services/docker/files/environment.yml|
|LUME_ENVIRONMENT__TMP_DIRECTORY                |string |/tmp/lume-services                                                                        |
|LUME_ENVIRONMENT__PLATFORM                     |string |linux-64                                                                                  |
|LUME_ENVIRONMENT__URL_RETRY_COUNT              |integer|                                                                                         3|
|LUME_ENVIRONMENT__PYTHON_VERSION               |string |3.9.13                                                                                    |


# Model Database
|                  Name                  | Type  |   Default   |
|----------------------------------------|-------|-------------|
|LUME_MODEL_DB__HOST                     |string |             |
|LUME_MODEL_DB__PORT                     |integer|             |
|LUME_MODEL_DB__USER                     |string |             |
|LUME_MODEL_DB__PASSWORD                 |string |             |
|LUME_MODEL_DB__DATABASE                 |string |             |
|LUME_MODEL_DB__CONNECTION__POOL_SIZE    |integer|             |
|LUME_MODEL_DB__CONNECTION__POOL_PRE_PING|boolean|True         |
|LUME_MODEL_DB__DIALECT_STR              |string |mysql+pymysql|


# Results Database
|             Name             | Type  |Default|
|------------------------------|-------|-------|
|LUME_RESULTS_DB__DATABASE     |string |       |
|LUME_RESULTS_DB__USERNAME     |string |       |
|LUME_RESULTS_DB__HOST         |string |       |
|LUME_RESULTS_DB__PASSWORD     |string |       |
|LUME_RESULTS_DB__PORT         |integer|       |
|LUME_RESULTS_DB__AUTHMECHANISM|string |DEFAULT|
|LUME_RESULTS_DB__OPTIONS      |object |{}     |


# Scheduling Service
|              Name              | Type  |           Default           |
|--------------------------------|-------|-----------------------------|
|LUME_PREFECT__SERVER__TAG       |string |core-1.4.0                   |
|LUME_PREFECT__SERVER__HOST      |string |http://localhost             |
|LUME_PREFECT__SERVER__HOST_PORT |string |4200                         |
|LUME_PREFECT__SERVER__HOST_IP   |string |127.0.0.1                    |
|LUME_PREFECT__UI__HOST          |string |http://localhost             |
|LUME_PREFECT__UI__HOST_PORT     |string |8080                         |
|LUME_PREFECT__UI__HOST_IP       |string |127.0.0.1                    |
|LUME_PREFECT__UI__APOLLO_URL    |string |http://localhost:4200/graphql|
|LUME_PREFECT__TELEMETRY__ENABLED|boolean|True                         |
|LUME_PREFECT__AGENT__HOST       |string |http://localhost             |
|LUME_PREFECT__AGENT__HOST_PORT  |string |5000                         |
|LUME_PREFECT__HOME_DIR          |string |~/.prefect                   |
|LUME_PREFECT__DEBUG             |boolean|False                        |
|LUME_PREFECT__BACKEND           |string |server                       |

