# Model packaging

Motivation... 

Templating allows us to ...

# steps
## 1. Create package repository

.json template


## 2. Define your model variables

Open `your-project/your_project/files/variables.yml`. The file will look like:

```yaml


```

## 3. Define your model evaluation method

This class is extensible and can accomodate as many additional methods as you'd like to include. 

## 4.  Define your flow

A minimal flow will accept ...


Execution of a flow is defined in the blurb: 
```python


```
Where `task1`, `task2`, and `task3` are defined in the module body using the `@task` decorator. 



Flow targets:
1. Filesystem target
2. Mongodb target

Flows are also extensible and can accomodate plenty of complexity. Using database targets requires a configured resources to be available to the flow at runtime. 


The `README.md` file should contain a comprehensive outline of variables accepted by your flow.

## 5. Actions

Define GitHub secret variables 




## Caveats
Because the repository is heavily templated, there are several things that may break on modification. The tests defined in the `your-project/your_project/tests` file are designed to test the following conditions:
1. Clearly defined entrypoints
2. Properly formatted and registerable flows
4. 