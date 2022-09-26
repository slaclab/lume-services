from setuptools import setup, find_packages
from os import path

cur_dir = path.abspath(path.dirname(__file__))

# parse requirements
with open(path.join(cur_dir, "requirements.txt"), "r") as f:
    requirements = f.read().split()

setup(
    name="lume-services-test-flows",
    description="Test flows for the lume-servicces project",
    packages=find_packages(),
    author="Jacqueline Garrahan",
    author_email="jgarra@slac.stanford.edu",
    license="SLAC Open",
    install_requires=requirements,
    url="https://github.com/slaclab/lume-services/lume_services/tests/flows",
    python_requires=">=3.8",
)
