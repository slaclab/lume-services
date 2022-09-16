from setuptools import setup, find_packages
from os import path
import versioneer

cur_dir = path.abspath(path.dirname(__file__))

# parse requirements
with open(path.join(cur_dir, "requirements.txt"), "r") as f:
    requirements = f.read().split()

setup(
    name="lume-services",
    description="A set of orchestration tools for the LUME project",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=find_packages(exclude=["*.tests"]),
    include_package_data=True,
    author="Jacqueline Garrahan",
    author_email="jgarra@slac.stanford.edu",
    license="SLAC Open",
    install_requires=requirements,
    url="https://github.com/slaclab/lume-services",
    python_requires=">=3.8",
    entry_points={"console_scripts": ["lume-services = lume_services.cli.cli:main"]},
)
