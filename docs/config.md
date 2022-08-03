# Configuration

LUME-services uses [injection](https://python-dependency-injector.ets-labs.org/) for runtime configuration of services. This means that programs can use the same code in a number of different environments simply by changing environment variable definitions.

Programs using the standard services packaged with LUME-services (the MongoDB implementation of Results Database, MySQL implementation of Model Registry), can use the configuration tools packaged with LUME-services directly by calling the configure script during code execution:
```
from lume_services.config import configure

# run configure by parsing LUME environment variables
configure()

```

LUME_MODEL_DB__HOST=127.0.0.1
LUME_MODEL_DB__USER=root
LUME_MODEL_DB__PASSWORD=test
LUME_MODEL_DB__PORT=3306
LUME_MODEL_DB__DATABASE=model_db
LUME_MODEL_DB__CONNECTION__POOL_SIZE=1
export LUME_PREFECT__SERVER__TAG=core-1.2.4
export LUME_PREFECT__SERVER__HOST_PORT=4200
export LUME_PREFECT__SERVER__HOST=127.0.0.1
export LUME_PREFECT__HASURA__HOST_PORT=3000
export LUME_PREFECT__HASURA__HOST=127.0.0.1
export LUME_PREFECT__GRAPHQL__HOST_PORT=4201
export LUME_PREFECT__GRAPHQL__HOST=127.0.0.1
export LUME_RESULTS_DB__HOST=127.0.0.1
export LUME_RESULTS_DB__PORT=27017
export LUME_RESULTS_DB__USERNAME=root
export LUME_RESULTS_DB__PASSWORD=password
export LUME_RESULTS_DB__DATABASE=test







## Overriding configuration values


```yaml
model:
  author: Jaqueline Garrhan
  laboratory: SLAC
  facility: LCLS
  beampath: cu_hxr
  description: Example model


deployment:
  version: v0.0
  source: https://github.com/jacquelinegarrahan/my-model-repo
  variables: my-model-repo/my_model_repo/files/variables.yaml
  flow_name: example_cu_hxr_0.0
```

```yaml
input_variables:
  input_variable_1:
    type: array

  input_variable_2:
    type: scalar

output_variables:
  output_variable_1:
    type: scalar

  output_variable_2:
    type: array

```



Multi-flow registration
```yaml
flow:
    order:
        - epics_pv_collection
        - scale
        - normalize
        - example_cu_hxr_0.0

epics: example_cu_hxr_epics_map.yaml
```




EPICS mapping.yaml
```yaml
flow:
    order:
        - name: epics_pv_collection
          config_file: example_cu_hxr_epics_map.yaml
        - name: scale
          factor: 5
        - name: normalize
        - name: example_cu_hxr_0.0

```

example_cu_hxr_epics_map.yaml
```yaml
input_variables:
  input_variable_1:
    pvname: test:input1
    protocol: pva

  input_variable_1:
    pvname: test:input2
    protocol: ca

output:
  pvname: test:output
  fields:
    - output_variable_1
    - output_variable_2

```
