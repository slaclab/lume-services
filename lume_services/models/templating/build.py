from cookiecutter.main import cookiecutter

# Create project from the cookiecutter-pypackage/ template
cookiecutter("cookiecutter-pypackage/")

# Create project from the cookiecutter-pypackage.git repo template
cookiecutter("https://github.com/audreyr/cookiecutter-pypackage.git")
