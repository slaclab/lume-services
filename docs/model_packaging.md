# Page TODO
- [ ] Fix variable types


# Model packaging (WIP docs)

The LUME project provides a standard interface for formatting models for use with LUME services in [LUME-model](https://slaclab.github.io/lume-model/). LUME-services relies on this interface for templating the user packages served over orchestration tooling. The formatting strategy consists of:


1. Model variables
2. Model execution class


## Variables
[LUME-model variables](https://slaclab.github.io/lume-model/variables/) define the inputs and outputs to the model and enforce minimal metadata on the variables. The variables are divided into categories, with `InputVariable` and `OutputVariable` as bases, then further subdivided by data type giving:

### INPUT VARIABLES
| Variable Type | Fields          | Type       | Description                                     | Required |
|---------------|-----------------|------------|-------------------------------------------------|----------|
| Scalar        | name            |            | Name assigned to the variable.                  | true     |
|               | default         |            | A default value                                 | true     |
|               | precision       |            | Precision to use for the value                  |          |
|               | value           |            | Value assigned to variable                      |          |
|               | value_range     |            | Range of values allowed.                        | true     |
|               | variable_type   |            | Assigned "scalar" on creation                   | true     |
|               | units           |            | String value for units                          |          | 
|               | parent_variable |            | Variable for which this is an attribute.        |          |
| Image         | name            | str        | Name assigned to the variable.                  | true     |
|               | default         |            | A default value                                 | true     |
|               | precision       | int        | Precision to use for the value                  |          |
|               | value           |            | Value assigned to variable                      |          |
|               | value_range     | list       | Range of values allowed.                        | true     |
|               | variable_type   |            | Assigned "image" on creation                    | true     |
|               | axis_labels     | List[str]  | Labels to use for rendering axes.               |          |
|               | axis_units      | List[str]  | Units to use for rendering axes labels.         |          | 
|               | x_min           | float      | Minimum x value of image.                       | true     |
|               | x_max           | float      | Maximum x value of image.                       | true     |
|               | y_min           | float      | Minimum y value of image.                       | true     |
|               | y_max           | float      | Maximum y value of image.                       | true     |
|               | x_min_variable  | str        | Scalar variable associated with image minimum x |          |
|               | x_max_variable  | str        | Scalar variable associated with image maximum x | true     |
|               | y_min_variable  | str        | Scalar variable associated with image minimum y |          |
|               | y_max_variable  | str        | Scalar variable associated with image maximum y |          |
| Array         | name            | str        | Name assigned to the variable.                  | true     |
|               | default         | np.ndarray | A default value                                 | true     |
|               | precision       | int        | Precision to use for the value                  |          |
|               | value           | np.ndarray | Value assigned to variable                      |          |
|               | value_range     | list       | Range of values allowed.                        | true     |
|               | variable_type   |            | Assigned "image" on creation                    | true     |
|               | dim_labels      | List[str]  | Labels to use for dimensions                    | true     |
|               | dim_units       | List[str]  | Units to use for dimensions.                    |          |


Output variables have the same fields as their corresponding input variables, but have less requirements than their input counterpart.

### OUTPUT VARIABLES
| Variable Type | Fields          | Type       | Description                                     | Required |
|---------------|-----------------|------------|-------------------------------------------------|----------|
| Scalar        | name            |            | Name assigned to the variable.                  | true     |
|               | default         |            | A default value                                 | true     |
|               | precision       |            | Precision to use for the value                  |          |
|               | value           |            | Value assigned to variable                      |          |
|               | value_range     |            | Range of values allowed.                        | true     |
|               | variable_type   |            | Assigned "scalar" on creation                   | true     |
|               | units           |            | String value for units                          |          | 
|               | parent_variable |            | Variable for which this is an attribute.        |          |
| Image         | name            | str        | Name assigned to the variable.                  | true     |
|               | default         |            | A default value                                 | true     |
|               | precision       | int        | Precision to use for the value                  |          |
|               | value           |            | Value assigned to variable                      |          |
|               | value_range     | list       | Range of values allowed.                        | true     |
|               | variable_type   |            | Assigned "image" on creation                    | true     |
|               | axis_labels     | List[str]  | Labels to use for rendering axes.               |          |
|               | axis_units      | List[str]  | Units to use for rendering axes labels.         |          | 
|               | x_min           | float      | Minimum x value of image.                       | true     |
|               | x_max           | float      | Maximum x value of image.                       | true     |
|               | y_min           | float      | Minimum y value of image.                       | true     |
|               | y_max           | float      | Maximum y value of image.                       | true     |
|               | x_min_variable  | str        | Scalar variable associated with image minimum x |          |
|               | x_max_variable  | str        | Scalar variable associated with image maximum x | true     |
|               | y_min_variable  | str        | Scalar variable associated with image minimum y |          |
|               | y_max_variable  | str        | Scalar variable associated with image maximum y |          |
| Array         | name            | str        | Name assigned to the variable.                  | true     |
|               | default         | np.ndarray | A default value                                 | true     |
|               | precision       | int        | Precision to use for the value                  |          |
|               | value           | np.ndarray | Value assigned to variable                      |          |
|               | value_range     | list       | Range of values allowed.                        | true     |
|               | variable_type   |            | Assigned "image" on creation                    | true     |
|               | dim_labels      | List[str]  | Labels to use for dimensions                    | true     |
|               | dim_units       | List[str]  | Units to use for dimensions.                    |          |

## Model

The LUME-model class provides a minimal and extensible base for formatting models. The ‘evaluate’ method must be implemented on the subclass and accept a dictionary mapping input variable name to LUME-model input variable. The output of the `evaluate` method will be the dictionary output. The example packaged in the [demo](demo.md) implements the following:

```python
import copy
from typing import Dict
import numpy as np
from lume_model.models import BaseModel
from lume_model.variables import InputVariable, OutputVariable
from my_model import INPUT_VARIABLES, OUTPUT_VARIABLES

class MyModel(BaseModel):
    input_variables = copy.deepcopy(INPUT_VARIABLES)
    output_variables = copy.deepcopy(OUTPUT_VARIABLES)

    def __init__(self, **settings_kwargs):
        """Initialize the model. If additional settings are required, they can be
        passed and handled here. For models that are wrapping model loads
        from other frameworks, this can be used for loading weights, referencing
        data files, etc.

        """
        super().__init__()

        # handle settings if any
        # if settings_kwargs is not None:
        # ...


    def evaluate(
        self, input_variables: Dict[str, InputVariable]
    ) -> Dict[str, OutputVariable]:
        """The evaluate method accepts input variables, performs the model execution,
        then returns a dictionary mapping variable name to output variable.

        Args:
            input_variables (Dict[str, InputVariable]): Dictionary of LUME-model input
                variables with values assigned.

        Returns:
            Dict[str, OutputVariable]: Dictionary of LUME-model output variables with
                values assigned.

        """

        self.output_variables["output1"].value = np.random.uniform(
            input_variables["input1"].value,  # lower dist bound
            input_variables["input2"].value,  # upper dist bound
            (50, 50),
        )
        self.output_variables["output2"].value = input_variables["input1"].value
        self.output_variables["output3"].value = input_variables["input2"].value


        return self.output_variables
```

The class can be extended to absorb other methods, accept custom kwargs, etc.

## Python Package

### Requirements
- Must include lume-services

No additional dependencies will be downloaded for pip packages. This means requirements must be defined in the environment.yaml...

# Templating
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


JSON FILE WITH THE FOLLOWING:
{% raw %}
```
{
  "author": "Jacqueline Garrahan",
  "email": "jacquelinegarrahan@gmail.com",
  "github_username": "jacquelinegarrahan",
  "project_name": "My Package", # Python importable package
  "project_slug": "{{ cookiecutter.project_name.lower().replace(' ', '_').replace('-', '_') }}",


  "project_short_description": "Python Boilerplate contains all the boilerplate you need to create a Python package.",
  "pypi_username": "{{ cookiecutter.github_username }}",
  "version": "0.1.0",
  "use_pytest": "n",
  "use_black": "n",
  "use_pypi_deployment_with_travis": "y",
  "add_pyup_badge": "n",
  "command_line_interface": ["Click", "Argparse", "No command-line interface"],
  "create_author_file": "y",
  "open_source_license": ["MIT license", "BSD license", "ISC license", "Apache Software License 2.0", "GNU General Public License v3", "Not open source"]
}


```
{% endraw %}
