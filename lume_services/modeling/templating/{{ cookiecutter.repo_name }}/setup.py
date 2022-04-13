from setuptools import setup, find_packages
from os import path
import versioneer

cur_dir = path.abspath(path.dirname(__file__))

# parse requirements
with open(path.join(cur_dir, "requirements.txt"), "r") as f:
    requirements = f.read().split()

# set up additional dev requirements
dev_requirements = []
with open(path.join(cur_dir, "dev-requirements.txt"), "r") as f:
    dev_requirements = f.read().split()

# set up additional dev requirements
docs_requirements = []
with open(path.join(cur_dir, "docs-requirements.txt"), "r") as f:
    docs_requirements = f.read().split()


setup(
    name="{{ cookiecutter.package_name }}",
    author="{{ cookiecutter.author }}",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=find_packages(),
  #  license="...",
    install_requires=requirements,
    extras_require={"dev": dev_requirements, "docs": docs_requirements},
    url="{{ cookiecutter.github_url }}",
    include_package_data=True,
    python_requires=">=3.7",
    entry_points = {
        "orchestration": [
            "{{ cookiecutter.project_slug }}.model={{ cookiecutter.project_slug }}.model:{{ cookiecutter.model_name }}",
            "{{ cookiecutter.project_slug }}.flow={{ cookiecutter.project_slug }}.flow.flow:{{ cookiecutter.model_name }}"
        ]
    }
)