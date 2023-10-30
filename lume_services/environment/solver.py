from importlib import import_module
from importlib_metadata import version
import os
import subprocess
import sys
import re
import yaml
import hashlib
import tarfile
from urllib.request import urlretrieve
from platform import python_version as current_python_version
from pydantic import BaseModel, root_validator
from typing import List
from typing import Optional, Literal
from pkginfo import SDist
import tempfile

from lume_services.errors import (
    UnableToInstallCondaDependenciesError,
    MissingEnvironmentYamlError,
    UnableToInstallPipDependenciesError,
    NoCondaEnvironmentFoundError,
)

import logging

logger = logging.getLogger(__name__)

# We use this template to check remote sources in
# Source.validate_source
_GITHUB_TARBALL_TEMPLATE = re.compile(
    r"^https://github.com/([a-z0-9_-]+)/([a-z0-9_-]+)/releases/download/([a-z0-9_.-]+)/([a-z0-9._-]+).tar.gz"  # noqa
)


VALID_KEYS = ("name", "dependencies", "prefix", "channels", "variables")


def validate_keys(data, kwargs):
    """Check for unknown keys, remove them and print a warning.

    The below is from: https://github.com/conda/conda/blob/main/conda_env/env.py
    license is added in this dir
    """
    invalid_keys = []
    new_data = data.copy() if data else {}
    for key in data.keys():
        if key not in VALID_KEYS:
            invalid_keys.append(key)
            new_data.pop(key)

    if invalid_keys:
        filename = kwargs.get("filename")
        verb = "are" if len(invalid_keys) != 1 else "is"
        plural = "s" if len(invalid_keys) != 1 else ""
        print(
            "\nEnvironmentSectionNotValid: The following section{plural} on "
            "'{filename}' {verb} invalid and will be ignored:"
            "".format(filename=filename, plural=plural, verb=verb)
        )
        for key in invalid_keys:
            print(" - {}".format(key))
        print("")

    deps = data.get("dependencies", [])
    depsplit = re.compile(r"[<>~\s=]")
    is_pip = lambda dep: "pip" in depsplit.split(dep)[0].split("::")  # noqa
    lists_pip = any(is_pip(_) for _ in deps if not isinstance(_, dict))
    for dep in deps:
        if isinstance(dep, dict) and "pip" in dep and not lists_pip:
            print(
                "Warning: you have pip-installed dependencies in your environment file, "  # noqa
                "but you do not list pip itself as one of your conda dependencies.  Conda "  # noqa
                "may not use the correct pip to install your packages, and they may end up "  # noqa
                "in the wrong place.  Please add an explicit pip dependency.  I'm adding one"  # noqa
                " for you, but still nagging you."
            )
            new_data["dependencies"].insert(0, "pip")
            break
    return new_data


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
        raise FileNotFoundError(environment_yaml_path)

    data = None
    with open(environment_yaml_path, "r") as f:
        data = yaml.safe_load(f)

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
    version: str
    name: str
    checksum: str
    image: Optional[str]
    conda_dependencies: List[str]
    channels: List[str]
    pip_dependencies: List[str]

    @root_validator(pre=True)
    def validate_source(cls, values):

        path = values.get("path")
        if path is None:
            raise ValueError(
                "must provide path to Source object. This is either the \
                filesystem path or the remote url."
            )

        if not isinstance(path, (str,)):
            raise ValueError("Provided path must be string. Provided %s", type(path))

        with tempfile.TemporaryDirectory() as tmpdirname:

            if not path[-7:] == ".tar.gz":
                raise ValueError("File passed for install %s is not a tgz file.", path)

            if os.path.exists(path):

                values["source_type"] = "file"
                tar_filename = path

            elif not _GITHUB_TARBALL_TEMPLATE.match(path):
                raise ValueError("Source does not match template %s", path)

            else:
                values["source_type"] = "url"
                # url is of form:
                # https://github.com/{USERNAME}/{REPO}/releases/download/{VERSION_TAG}/{REPO}-{VERSION_TAG}.tar.gz # noqa
                # can use index to extract name and version:
                url_split = path.split("/")
                tmp_filename = url_split[-1]
                tar_filename = f"{tmpdirname}/{tmp_filename}"

                try:
                    urlretrieve(
                        path, filename=tar_filename
                    )  # NEED TO HANDLE PRIVATE REPOS
                    logger.info("%s saved to %s", path, tar_filename)
                except Exception as e:
                    logger.error("Unable to download source %s", path)
                    raise e

            # get package info from tarball
            pkg = SDist(tar_filename)
            version = pkg.version
            name = pkg.name

            # compute checksum
            checksum = hashlib.sha256(open(tar_filename, "rb").read()).hexdigest()
            # untar the file
            base_name = tar_filename.split("/")[-1].replace(".tar.gz", "")
            with tarfile.open(tar_filename) as f:
                extract_path = f"{tmpdirname}/{base_name}"

                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner) 
                    
                
                safe_extract(f, tmpdirname)

                # if its a directory, check that the environment yaml is found
                env_yaml_path = f"{extract_path}/environment.yml"
                if not os.path.isfile(env_yaml_path):
                    raise MissingEnvironmentYamlError(extract_path)

                (
                    channels,
                    conda_dependencies,
                    pip_dependencies,
                ) = load_environment_yaml(env_yaml_path)

        values["version"] = version
        values["name"] = name
        values["conda_dependencies"] = conda_dependencies
        values["pip_dependencies"] = pip_dependencies
        values["channels"] = channels
        values["checksum"] = checksum

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
        model_mod = None
        # if the prefix isn't set
        if not prefix:
            raise NoCondaEnvironmentFoundError()

        # check that already installed
        try:
            pkg_version = version(self.name)
            if pkg_version is not None:

                if pkg_version == self.version:
                    logger.info(
                        "Version %s of %s already installed.", pkg_version, self.name
                    )

                    image_mod = import_module(f"{self.name}._image")
                    self.image = image_mod.IMAGE
                    return
                else:
                    logger.debug("Uninstalling old model")
                    uninstall_proc = subprocess.check_output(
                        [sys.executable, "-m", "pip", "uninstall", "-y", self.name]
                    )

                    output_lines = uninstall_proc.decode("utf-8").split("\n")
                    for line in output_lines:
                        logger.debug(line)

                    logger.info("Uninstall complete")

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
        ]

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
            except subprocess.CalledProcessError:
                raise UnableToInstallCondaDependenciesError(conda_dependencies)

            logger.debug("installing pip deps")
            with tempfile.TemporaryDirectory() as tmpdirname:
                base_filename = self.path.split("/")[-1]
                filename = base_filename

                if self.source_type == "url":
                    base_filename = self.path.split("/")[-1]
                    filename = f"{tmpdirname}/{base_filename}"

                    try:
                        urlretrieve(
                            self.path, filename=filename
                        )  # NEED TO HANDLE PRIVATE REPOS
                        logger.info("%s saved to %s", self.path, filename)
                    except Exception as e:
                        logger.error("Unable to download source %s", self.path)
                        raise e

                    pip_dependencies = pip_dependencies + [filename]

                else:
                    pip_dependencies = pip_dependencies + [self.path]

                pip_cmd = [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--no-deps",
                    "-v",
                ] + pip_dependencies

                print(pip_cmd)

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
            model_mod = import_module(self.name)

            if not model_mod.__version__ == self.version:

                raise ValueError(
                    "Import module verison incorrect. Expected %s got %s.",
                    self.version,
                    model_mod.__version__,
                )

            image_mod = import_module(f"{self.name}._image")
            self.image = image_mod.IMAGE

            return
