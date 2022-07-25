from {{ cookiecutter.project_slug }}.flow import get_flow

def test_local_flow(data):
    flow = get_flow()
    flow.run(**data)

    try:
        flow.run(**data)

    except ValueError as err:
        raise ValueError("Flow was evaluated with a missing parameter value. You've likely added additional flow inputs with defaults not specified and tests have not been modified to account for those changes.")
