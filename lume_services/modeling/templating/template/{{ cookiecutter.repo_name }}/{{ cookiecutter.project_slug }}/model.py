from lume_model.model import BaseModel
from pkg_resources import resource_filename
from lume_model.utils import variables_from_yaml
from lume_model.variables import InputVariable, OutputVariable
from typing import Dict

VARIABLE_FILE =resource_filename(
    "{{ cookiecutter.project_slug }}.files", "variables.yml"
)

INPUT_VARIABLES, OUTPUT_VARIABLES = variables_from_yaml(VARIABLE_FILE)


class {{ cookiecutter.model_class }}(BaseModel):
    def __init__(self):
        self.input_variables = INPUT_VARIABLES
        self.output_variables = OUTPUT_VARIABLES

    def evaluate(self, input_variables: Dict[str, InputVariable]) -> Dict[str, OutputVariable]:
        """Class method for evaluating and storing new input and output variables
        
        """
        self.input_variables = input_variables

        # Assign output variables a value based on your execution
        model_output_dict = ...

        for output_varname, value in model_output_dict.items():
            self.output_variables[output_varname].value = value

        return self.output_variables
