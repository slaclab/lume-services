# Configuration

LUME-services uses [injection](https://python-dependency-injector.ets-labs.org/) for runtime configuration of services. This means that programs can use the same code in a number of different environments simply by changing environment variable definitions.

Programs using the standard services packaged with LUME-services (the MongoDB implementation of Results Database, Model Database sqlalchemy), can use the configuration tools packaged with LUME-services directly by calling the configure script during code execution:
```
from lume_services.config import configure, LUMEServicesSettings

lume_services_settings = LUMEServicesSettings(



)


# run configure by parsing LUME environment variables
configure()

# run configure with manual configuration
...

```

The user may also configure their environment by taking advantage of the environment configuration feature.

{% include 'files/env_vars.md' %}


## Submitting workflows with the appropriate configuration
you may elect to change env vars on your submitted jobs
Configuration of the job environment must respect hostnames available to their own networks





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
