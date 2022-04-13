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
    name="lume-services",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=find_packages(),
    author="SLAC National Accelerator Laboratory",
    author_email="jgarra@slac.stanford.edu",
    license="SLAC Open",
    install_requires=requirements,

    # Add extra requirements
    extras_require={"dev": dev_requirements, "docs": docs_requirements},
    url="https://github.com/slaclab/lume-services",
    include_package_data=True,
    python_requires=">=3.7",
   # entry_points={
   #     "console_scripts": [
   #     ]
   # },
)