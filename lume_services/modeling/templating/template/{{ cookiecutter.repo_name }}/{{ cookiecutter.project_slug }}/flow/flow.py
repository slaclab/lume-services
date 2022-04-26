from prefect import Flow, task
from prefect import Parameter

from lume_services.scheduling.prefect.results import MongoDBResult
from prefect.tasks.control_flow import case
import os

from {{ cookiecutter.project_slug }}.model import {{ cookiecutter.model_class }}
from {{ cookiecutter.project_slug }} import INPUT_VARIABLES, service_container

import copy



@task(log_stdout=True)
def format_input_vars(**input_variable_parameter_dict):
    """Assumes input_var_rep is a dict mapping var_name to value. The input variables have already been instantiated, so here we assign their values. 
    
    """ 
    input_variables = copy.deepcopy(INPUT_VARIABLES)

    for var_name in INPUT_VARIABLES:
        input_variables[var_name].value = input_variable_parameter_dict[var_name]

    return input_variables


@task(log_stdout=True)
def model_predict(formatted_input_vars, settings):

    model = {{ cookiecutter.model_class }}(**settings)

    return model.execute(input_variables)

@task(result=MongoDBResult(model_type="impact", results_db=service_container.results_db()))
def store_db_results(model_predict_results):

    # format your results into a serializable structure
    dat = {
        "output_variables": {
            var_name: var.json() for var_name, var in model_predict_results["output_variables"]
        },
     #   "output_filename": ...
    }

    return dat

#@task(result=FileResult)
#def store_result_artifact(model_predict_results):
#    return model_predict_results["output_filename"]


with Flow(
        {{ cookiecutter.repo_name }},
    ) as flow:


    preprocess_variables = Parameter("preprocess_variables", default=False)
    input_variable_parameter_dict = {
        var_name: Parameter(var_name, default=var.default) for var, var_name in INPUT_VARIABLES.items()
    }

    with case(preprocess_variables, True):
        


    model_settings = Parameter("model_settings", default=None)

    # Define any extra parameters here...

    # Define flow DAG
    # Can expand this for extended functionality
    formatted_input_vars = format_input_vars(**input_variable_parameter_dict)
    model_output = model_predict(formatted_input_vars, model_settings)
    store_db_results(model_output) 
    store_result_artifact(model_output)


def get_flow():
    return flow
