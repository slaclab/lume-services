# Model packaging

Motivation...

Templating allows us to ...



Because we've chosen the approach of having a single docker image representing our body of models,



## Requirements
- Must include lume-services

No additional dependencies will be downloaded for pip packages. This means requirements must be defined in the environment.yaml...

# steps
## 1. Create package repository

.json template



```yaml

"cookiecutter.project_slug"
├─ .github/
|  ├─ workflows/
|  |  ├─ build_image.yaml
|  |  ├─ build_image_scr.yml
│  │  ├─ tests.yaml
│  │  ├─ build.yaml
├─ "cookiecutter.package"
|  ├─ files/
|  |  ├─ __init__.py
|  |  ├─ variables.yaml
|  ├─ tests/
|  |  ├─ test_flow.py
|  ├─ __init__.py
|  ├─ config.py
|  ├─ model.py
|  ├─ flow.py
├─ _entrypoint.sh
├─ .gitignore
├─ conftest.py
├─ dev-environment.yml
├─ Dockerfile
├─ environment.yml
├─ MANIFEST.in
├─ pytest.ini
├─ requirements.txt
├─ setup.cfg
├─ setup.py

```




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
