from {{ cookiecutter.project_slug }}.model import {{ cookiecutter.model_class }}

def test_model():
    """Minimal test of model execution using the defaults save on input variables.
    
    """
    model = {{ cookiecutter.model_class }}()
    input_vars = {{ cookiecutter.model_class }}.input_variables

    # use default for execution
    for var in input_vars:
        input_vars[var].value = input_vars[var].value

    model.execute(input_vars)
