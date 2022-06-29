# {{ cookiecutter.repo_name }}

This repository packages the `{{ cookiecutter.model_class }}` in `{{ cookiecutter.project_slug }}/model.py ` for execution with [Prefect](https://docs.prefect.io/) using the flow described in `{{ cookiecutter.project_slug }}/flow/flow.py`. 


## Installation

This package may be installed using pip:
```
pip install git+{{ cookiecutter.github_url }}
```

## Use

You may run the flow locally using:
```python
from {{ cookiecutter.project_slug }}.flow import get_flow

flow = get_flow()
flow.run(data)

```

## Dev

Create an environment using the environment.yml packaged with the repository:
```
conda env create -f environment.yml
```
Activate your environment:
```
conda activate {{ cookiecutter.project_slug }}
```
Install dev requirements:
```
conda install --file dev-requirements.txt
```

Install editable package:
```
pip install -e .
```

Tests can be executed from the root directory using:
```
pytest .
```


## Visualize flow


![Screenshot](docs/flow.png)



### Note
This README was automatically generated using the template defined in https://github.com/slaclab/lume-services/lume_services/modeling/templating with the following configuration:

```json
{
    "author": "{{ cookiecutter.author }}",
    "email": "{{ cookiecutter.email }}",
    "github_username": "{{ cookiecutter.github_username }}",
    "github_url": "{{ cookiecutter.github_url }}",
    "project_name": "{{ cookiecutter.project_name }}", 
    "repo_name": "{{ cookiecutter.repo_name }}", 
    "project_slug": "{{ cookiecutter.project_slug }}",
    "model_class": "{{ cookiecutter.model_class }}"
}
```
