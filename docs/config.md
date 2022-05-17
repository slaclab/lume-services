# Configuration



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