from importlib import import_module
import os
import json
import urllib
import subprocess
import sys
import re
import hashlib
from contextlib import contextmanager
from platform import python_version as current_python_version
from xml.dom.expatbuilder import parseFragmentString
from pydantic import BaseModel, root_validator
from typing import List
from typing import Optional, Literal
import tarfile
from pkginfo import SDist

from conda_env.env import yaml_safe_load, validate_keys
from conda.exceptions import EnvironmentFileNotFound

import shutil
from conda.cli.python_api import run_command

from lume_services.docker.files import ENVIRONMENT_YAML
from lume_services.errors import (
    WritePermissionError,
    NoPackagesToInstallError,
    UnableToInstallCondaDependenciesError,
    UnableToIndexLocalChannelError,
    MissingEnvironmentYamlError,
    UnableToInstallPipDependenciesError,
    NoCondaEnvironmentFoundError,
)

from lume_services.utils import select_python_version

import logging

logger = logging.getLogger(__name__)

# We use this template to check remote sources in
# Source.validate_source
_GITHUB_TARBALL_TEMPLATE = re.compile(
    r"^https://github.com/([a-z0-9_-]+)/([a-z0-9_-]+)l/releases/download/([a-z0-9_.-]+)/([a-z0-9._-]+).tar.gz"  # noqa
)


@contextmanager
def temp_conda_env(env_path: str, prefix: str = "tmp_env") -> None:
    """Context manager for creating transient conda environments. At exit, the
    environment is removed.

    Args:
        env_path (str): Path to directory used for storing conda environments.
        prefix (str): Prefix used for creating the conda environment.

    Yields:
        str: Full local path to the prefixed environment.

    """
    if not os.path.isdir(env_path):
        raise FileNotFoundError(env_path)

    full_prefix = f"{env_path}/{prefix}"

    # Run conda creation command
    run_command("create", "-p", full_prefix, use_exception_handler=False)

    try:
        yield full_prefix
    finally:
        shutil.rmtree(f"{env_path}/{prefix}")


def load_environment_yaml(environment_yaml_path: str):
    """Load a conda environment.yml file and parse into channels, conda
    dependencies, and pip dependencies.

    Args:
        environment_yaml (str): String path to environment yaml.

    Returns:
        tuple: Three element tuple of channels, conda_dependencies, and
            pip_dependencies

    Raises:
        EnvironmentFileNotFound: File does not exist.
        ValueError: Unsupported list of sub dependencies provided. At present, only
            support pip lists.

    """
    if not os.path.isfile(environment_yaml_path):
        raise EnvironmentFileNotFound(environment_yaml_path)

    data = None
    with open(environment_yaml_path, "r") as f:
        data = yaml_safe_load(f)

    data = validate_keys(data, {})
    channels = data["channels"]
    dependencies = data["dependencies"]
    conda_dependencies = []
    pip_dependencies = []

    for dep in dependencies:
        if isinstance(dep, (str,)):
            conda_dependencies.append(dep)

        elif isinstance(dep, (dict,)):
            for key, value in dep.items():
                if key == "pip":
                    pip_dependencies += value

                else:
                    raise ValueError("Unsupported dependencies: %s", key)

    return channels, conda_dependencies, pip_dependencies


class Source(BaseModel):
    """

    Attributes:
        source_type (Literal["file", "url"])
        path (str): Sources can be provided by either a file path to a local resource
            or a GitHub url to a release tarball with the form: https://github.com/{USERNAME}/{REPO}/releases/download/{VERSION_TAG}/{REPO}-{VERSION_TAG}.tar.gz
            These sources must be fromatted in compliance with the LUME-services model
            standard. See: https://slaclab.github.io/lume-services/model_packaging/
        tar_filename (Optional[str]):
        pkg_dir (str):
        version
        name
        checksum
        image
        tmp_dir

    """  # noqa

    path: str
    source_type: Literal["file", "url"]
    tar_filename: str
    pkg_dir: str
    version: str
    name: str
    checksum: str
    image: Optional[str]
    tmp_dir: str = "/tmp/lume-services/sources"
    conda_dependencies: List[str]
    channels: List[str]
    pip_dependencies: List[str]

    @root_validator(pre=True)
    def validate_source(cls, values):

        tmp_dir = values.get("tmp_dir")
        if tmp_dir is None:
            tmp_dir = cls.__fields__["tmp_dir"].default

        # create temporary directory
        if not os.path.exists(tmp_dir):
            os.mkdir(tmp_dir)

        path = values.get("path")
        if path is None:
            raise ValueError(
                "must provide path to Source object. This is either the \
                filesystem path or the remote url."
            )

        if isinstance(path, (str,)):

            if os.path.exists(path):

                # if its a directory, check that the environment yaml is found
                if not os.path.isfile(f"{path}/environment.yml"):
                    raise MissingEnvironmentYamlError(path)

                values["source_type"] = "file"
                tar_filename = path

                # get repo and tag
                pkg = SDist(path)
                version = pkg.version
                name = pkg.name

            elif not _GITHUB_TARBALL_TEMPLATE.match(path):
                raise ValueError("Source does not match template %s", path)

            else:
                values["source_type"] = "url"
                # url is of form:
                # https://github.com/{USERNAME}/{REPO}/releases/download/{VERSION_TAG}/{REPO}-{VERSION_TAG}.tar.gz # noqa
                # can use index to extract name and version:
                url_split = path.split("/")
                tmp_filename = url_split[-1]
                tar_filename = f"{tmp_dir}/{tmp_filename}"

                try:
                    urllib.request.urlretrieve(
                        path, filename=tar_filename
                    )  # NEED TO HANDLE PRIVATE REPOS
                    logger.info("%s saved to %s", path, tar_filename)
                except Exception as e:
                    logger.error("Unable to download source %s", path)
                    raise e

                pkg = SDist(tar_filename)
                version = pkg.version
                name = pkg.name

                tar_filename = f"{tmp_dir}/{name}-{version}.tar.gz"

            # compute sha256 checksum
            checksum = hashlib.sha256(open(tar_filename, "rb").read()).hexdigest()
            values["checksum"] = checksum
            values["tar_filename"] = tar_filename
            values["version"] = version
            values["name"] = name

        # now untar
        with tarfile.open(tar_filename) as f:
            # extracting will create a subdir for each member.
            # This should be the top level of the repo

            f.extractall(tmp_dir)

        extract_path = f"{tmp_dir}/{name}-{version}"
        values["pkg_dir"] = extract_path

        env_yaml_path = f"{extract_path}/environment.yml"
        channels, conda_dependencies, pip_dependencies = load_environment_yaml(
            env_yaml_path
        )
        values["conda_dependencies"] = conda_dependencies
        values["pip_dependencies"] = pip_dependencies
        values["channels"] = channels

        return values

    def install(
        self,
        dry_run: bool = False,
    ) -> None:
        """Install the source.

        Args:
            dry_run (bool): Whether to perform dry run installation. If True, will log
                dependencies that would have been installed.

        Raises:
            NoCondaEnvironmentFoundError: Cannot find active conda environment
            UnableToInstallCondaDependenciesError: Error encounted while installing
                conda dependencies.
            UnableToInstallPipDependenciesError: Error encountered while installing
                pip dependencies.


        """

        # get prefix
        prefix = os.environ.get("CONDA_PREFIX")

        # if the prefix isn't set
        if not prefix:
            raise NoCondaEnvironmentFoundError()

        # check that already installed
        try:
            model_mod = import_module(self.name)

            if model_mod is not None:
                v = model_mod.__version__
                if v == self.version:
                    logger.info("Version %s of %s already installed.", v, self.name)
                    return

        # continue if not found
        except ModuleNotFoundError:
            pass

        # filter python
        conda_dependencies = [
            dep for dep in self.conda_dependencies if "python" not in dep
        ]

        # filter lume-services and add file
        pip_dependencies = [
            dep for dep in self.pip_dependencies if "lume-services" not in dep
        ] + [self.tar_filename]

        # install dependencies
        if dry_run:
            pip_dep_strings = [f"    {dep}" + "\n" for dep in pip_dependencies]
            conda_dep_strings = [f"    {dep}" + "\n" for dep in conda_dependencies]

            logger.info("Pip dependencies are: \n%s", "".join(pip_dep_strings))
            print(f"Pip dependencies are: \n{''.join(pip_dep_strings)}")
            logger.info("Conda dependencies are: \n%s", "".join(conda_dep_strings))
            print(f"Conda dependencies are: \n {''.join(conda_dep_strings)}")

        else:
            logger.info("Installing dependencies...")

            logger.debug("installing conda deps")

            conda_cmd = ["conda", "install", "-y"]
            for channel in self.channels:
                conda_cmd += ["-c", channel]

            conda_cmd += conda_dependencies

            try:
                logger.debug("Opening subprocess")
                download_proc = subprocess.check_output(conda_cmd)

                output_lines = download_proc.decode("utf-8").split("\n")
                for line in output_lines:
                    logger.debug(line)

                logger.info("Dependency installation complete")
            except subprocess.CalledProcessError as e:
                raise UnableToInstallCondaDependenciesError(conda_dependencies)

            logger.debug("installing pip deps")
            # run verbose
            pip_cmd = [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-deps",
                "-v",
            ] + pip_dependencies

            # run pip command
            try:
                logger.debug("Opening subprocess")
                download_proc = subprocess.check_output(pip_cmd)

                output_lines = download_proc.decode("utf-8").split("\n")
                for line in output_lines:
                    logger.debug(line)

                logger.info("Dependency installation complete")

            except subprocess.CalledProcessError as e:
                raise UnableToInstallPipDependenciesError(
                    pip_dependencies, current_python_version(), sys.platform, e
                )

            # confirm import successful and get image from the _image.py module
            # packaged with the template
            image_mod = import_module(f"{self.name}._image")
            self.image = image_mod.IMAGE

            return
