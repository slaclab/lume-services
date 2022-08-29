import os
import json
import urllib
import subprocess
import sys
import re
from contextlib import contextmanager
from mamba.api import MambaSolver
import libmambapy
from pydantic import BaseModel, root_validator
from typing import List
import pathlib
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
    NoCondaEnvironmentFoundError
)

from lume_services.utils import select_python_version

import logging

logger = logging.getLogger(__name__)

# We use this template to check remote sources in
# EnvironmentResolverConfig.validate_source
_GITHUB_TARBALL_TEMPLATE = re.compile(
    r"^https://api.github.com/repos/([a-z0-9_-]+)/([a-z0-9_-]+)/tarball/([a-z0-9_-]+)"
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


class EnvironmentResolverConfig(BaseModel):
    """Configuration for the EnvironmentResolver class.

    Attributes:
        local_pip_directory (str): Path to local pip repository.
        local_conda_channel_directory (str): Directory of local conda channel where
            dependencies will be downloaded to and registered with.
        base_env_filepath (Optional[str]): Optional string for indicating base
            environment specs. This defaults to the environment defined in
            `lume_services/docker/files/environment.yml`.
        tmp_directory (str): Temp directory for storing temporary conda
            environment during resolution. The temp directory does not have to exist
            on initialization, but does require write permissions to parent
            directories.
        platform (Literal["linux-64", "linux-32", "osx-64", "win-32", "win-64"]):
            conda-build platform target, see: https://docs.conda.io/projects/conda-build/en/latest/user-guide/tutorials/build-pkgs.html#converting-a-package-for-use-on-all-platforms
        url_retry_count (int): Number of times to retry a download when fetching url.
        source_type (Literal["file", "url"])
        python_version (str): Fallback python version if no python specified in 
            environment.yml

    """  # noqa

    local_pip_directory: str
    local_conda_channel_directory: str
    base_env_filepath: Optional[str] = ENVIRONMENT_YAML
    tmp_directory: str = "/tmp/lume-services"
    platform: Literal["linux-64", "linux-32", "osx-64", "win-32", "win-64"] = "linux-64"
    url_retry_count: int = 3
    python_version: str = sys.version


class Source(BaseModel):
    """
    
    Attributes:
        source_type (Literal["file", "url"])
        path (str): Sources can be provided by either a file path to a local resource
            or a GitHub url to a release tarball with the form  https://api.github.com/repos/{USERNAME}/{REPO}/tarball/{VERSION_TAG}
            These sources must be fromatted in compliance with the LUME-services model
            standard. See: https://slaclab.github.io/lume-services/model_packaging/
    
    """
    path: str
    source_type: Literal["file", "url"]

    @root_validator(pre=True)
    def validate_source(cls, values):

        path = values.get("path")

        if isinstance(path, (str,)):

            if os.path.exists(path):

                # if its a directory, check that the environment yaml is found
                if not os.path.isfile(f"{path}/environment.yml"):
                    raise MissingEnvironmentYamlError(path)

                values["source_type"] = "file"

            elif not _GITHUB_TARBALL_TEMPLATE.match(path):
                raise ValueError("Source does not match template %s", path)

            else:
                values["source_type"] = "url"

        return values


class EnvironmentResolver:
    """The EnvironementResolver class is used to manage dependencies for models.
    Must be run by a user that has read/write permissions to the local channel path and
    tmp_path. The resolver accomadates a set of base dependencies that it loads from
    the `base_env_filepath` on the config object.

    """

    def __init__(self, config: EnvironmentResolverConfig):
        """
        Args:
            config (EnvironmentResolverConfig): Resolver configuration

        Raises:
            EnvironmentFileNotFound: The environment file provided for configuring base
                environment does not exist.
            OSError: Error encountered during creation of temporary directory.
            WritePermissionError: No write permissions for this user to temporary
                directory or local conda channel.
            FileNotFoundError: Directory for local conda channel not found.

        """
        self.config = config
        self._base_channels = []
        self._base_conda_dependencies = []
        self._base_pip_dependencies = []
        self._platform = config.platform
        self._local_conda_channel_directory = config.local_conda_channel_directory
        self._local_pip_directory = config.local_pip_directory
        self._base_env_filepath = config.base_env_filepath
        self._tmp_directory = config.tmp_directory
        self._url_retry_count = config.url_retry_count
        self._active_python_version = sys.version

        if config.base_env_filepath is not None:
            (
                self._base_channels,
                self._base_conda_dependencies,
                self._base_pip_dependencies,
            ) = load_environment_yaml(self._base_env_filepath)

        # check existence of directory
        if not os.path.isdir(self._tmp_directory):
            logger.warning("%s is not a directory. Creating...", self._tmp_directory)
            try:
                os.mkdir(self._tmp_directory)
            except OSError as error:
                logger.error(error)
                raise error

        if not os.access(self._tmp_directory, os.X_OK | os.W_OK):
            raise WritePermissionError(self._tmp_directory)

        # check existence of local channel
        if not os.path.isdir(self._local_conda_channel_directory):
            logger.error("%s is not a directory.", self._local_conda_channel_directory)
            raise FileNotFoundError(self._local_conda_channel_directory)

        if not os.access(self._local_conda_channel_directory, os.X_OK | os.W_OK):
            raise WritePermissionError(self._local_conda_channel_directory)


    def solve(
        self,
        source_path: str,
        continue_on_fail: bool = False,
        rollback: bool = True,
        dry_run: bool = False,
    ):
        """
        Args:
            source_path (str): Path to local or remote source
            continue_on_fail (bool): Whether to continue installation if a file cannot
                be downloaded.
            rollback (bool): Whether to remove all installed packages on installation
                fail.
            dry_run (bool): Dry runs will not install dependencies, but rather log the
                dependency output to the CLI.


        Returns:
            Union[None, dict]: Returns none if dry-run instalation. Returns dictionary
                of installed dependencies otherwise.

        """
        tar_filepath, pkg_dir = self._prepare_source(source_path=source_path)

        # collect environment.yml
        # Try with both .yaml and .yml
        env_yaml_path = f"{pkg_dir}/environment.yml"
        if not os.path.isfile(f"{pkg_dir}/environment.yml"):
            env_yaml_path = f"{pkg_dir}/environment.yaml"

        # run resolution on file
        dependencies = self._resolve_dependencies(
            env_yaml_path,
            self._platform,
            use_temp = True
        )

        # add source to pip dependendencies
        dependencies["pip"].append(tar_filepath)


        # install dependencies
        if dry_run:
            pip_dep_strings = [f"    {dep['name']}: {dep['version']}" for dep in dependencies["pip"]]
            conda_dep_strings = [    f"{dep['name']}: {dep['version']}" for dep in dependencies["conda"]]

            logger.info("Environment solved for %s using Python=%s on %s", source_path, dependencies["python_version"], self._platform)
            logger.info("Pip dependencies are: \n%s", "\n".join(pip_dep_strings))
            logger.info("Conda dependencies are: \n%s", "\n".join(conda_dep_strings))

            return 

        else:
            logger.info("Installing dependencies...")
            # install and conda dependencies
            with temp_conda_env(self._tmp_directory, "tmp_env"):
                installed_conda = self._install_conda_dependencies_to_local_channel(
                    dependencies["conda"],
                    continue_on_fail=continue_on_fail,
                    rollback=rollback,
                )

            installed_pip = self._install_pip_dependencies_to_local_repo(
                dependencies["pip"], python_version=dependencies["python_version"], platform = self._platform
            )
            logger.info("Dependency installation complete")

            logger.debug("Moving source to pip directory: %s", tar_filepath)

            tar_filename = tar_filepath.split("/")[-1]

            shutil.move(tar_filepath, f"{self._local_pip_directory}/{tar_filename}")
            logger.info("Instaled source to local pip repo.")

            return {"pip": installed_pip, "conda": installed_conda}

    
    def install(self, source_path: str,
        dry_run: bool = False,
    ):
        """
        Args:
            source_path (str): Path to local or remote source
            dry_run (bool): Whether to perform dry run installation. If True, will log
                dependencies that would have been installed.

        Returns:
            Union[None, dict]: Returns none if dry-run instalation. Returns dictionary
                of installed dependencies otherwise.

        """

        # get prefix
        prefix = os.environ.get("CONDA_PREFIX")

        # if the prefix isn't set
        if not prefix:
            raise NoCondaEnvironmentFoundError()

        # prepare source
        tar_filepath, pkg_dir = self._prepare_source(source_path=source_path)

        # collect environment.yml
        # Try with both .yaml and .yml
        env_yaml_path = f"{pkg_dir}/environment.yml"
        if not os.path.isfile(f"{pkg_dir}/environment.yml"):
            env_yaml_path = f"{pkg_dir}/environment.yaml"

        dependencies = self._resolve_dependencies(env_yaml_path, platform=None, use_temp=False)

        # add source to pip dependendencies
        dependencies["pip"].append(tar_filepath)

        # install dependencies
        if dry_run:
            pip_dep_strings = [f"    {dep['name']}: {dep['version']}" for dep in dependencies["pip"]]
            conda_dep_strings = [    f"{dep['name']}: {dep['version']}" for dep in dependencies["conda"]]

            logger.info("Environment solved for %s using Python=%s on %s", source_path, dependencies["python_version"], sys.platform)
            logger.info("Pip dependencies are: \n%s", "\n".join(pip_dep_strings))
            logger.info("Conda dependencies are: \n%s", "\n".join(conda_dep_strings))

            return 

        else:
            logger.info("Installing dependencies...")

            # install conda dependencies
            dependencies["conda_transaction"].execute(libmambapy.PrefixData(str(prefix)))

            # run verbose
            pip_cmd = (
                [sys.executable, "-m", "pip", "install" "--yes", "--no-deps", "-v"]
                + dependencies["pip"]
            )

            # run pip command
            try:
                download_proc = subprocess.check_output(
                    pip_cmd
                )

                output_lines = download_proc.decode("utf-8").split("\n")
                for line in output_lines:
                    logger.debug(line)

                logger.info("Dependency installation complete")

            except subprocess.CalledProcessError as e:
                raise UnableToInstallPipDependenciesError(
                    dependencies["pip"], sys.version, sys.platform, e
                )


    def _prepare_source(self, source_path) -> tuple:
        """Prepare source from tarball. If source is remote, will request download of
        artifact.

        Args:
            source_path (str): Path to local or remote source

        """
        source = Source(path=source_path)

        if source.source_type == "url":
            # url is of form:
            # https://api.github.com/repos/jacquelinegarrahan/my-model/tarball/v0.0
            # can use index to extract name and version:
            url_split = source.path.split("/")
            repo = url_split[-3]
            tag = url_split[-1]
            tar_filename = f"{self._tmp_directory}/{repo}-{tag}.tar.gz"
            untar_dir = f"{self._tmp_directory}/{repo}-{tag}"

            try:
                urllib.request.urlretrieve(source.path, filename=tar_filename)
                logger.info("%s saved to %s", source.path, tar_filename)
            except Exception as e:
                logger.error("Unable to download souce %s", source.path)
                raise e

        # source type is file
        else:
            tar_filename = source.path
            untar_dir = source.path.replace(".tar.gz", "")

        # untar the directory
        with tarfile.open(tar_filename) as f:
            # extracting will create a subdir for each member.
            # This should be the top level of the repo
            extract_subdir = f.getmembers()[0].name
            f.extractall(untar_dir)

        return tar_filename, f"{untar_dir}/{extract_subdir}"

    def _resolve_dependencies(self, environment_yaml_path: str, platform: Literal["linux-64", "linux-32", "osx-64", "win-32", "win-64"], use_temp=True) -> dict:
        """Solves environment

        Args:
            environment_yaml_path (str): String path to the environment YAML.
            platform (Literal["linux-64", "linux-32", "osx-64", "win-32", "win-64"]):
            conda-build platform target, see: https://docs.conda.io/projects/conda-build/en/latest/user-guide/tutorials/build-pkgs.html#converting-a-package-for-use-on-all-platforms
            use_temp (bool): Whether to use a temporary environment for dependency resolution.

        Returns:
            dict: Dictionary of the form:
                {"pip": ..., "conda": ..., "python_version": ...}

        """ # noqa
        channels, conda_dependencies, pip_dependencies = load_environment_yaml(
            environment_yaml_path
        )

        # build pip dependencies
        pip_dependencies = list(set(self._base_pip_dependencies + pip_dependencies))

        if use_temp:
            channels = list(set(self._base_channels + channels))
            logger.info(
                "Using conda channels %s to install dependencies.", ", ".join(channels)
            )

            # filter python dependency from the base environment
            python_version_str = None
            for dep in self._base_conda_dependencies:
                if "python" in dep:
                    python_version_str = dep.replace("python", "")
                    break

            for dep in conda_dependencies:
                if "python" in dep:
                    python_version_str = dep.replace("python", "")
                    break

            python_version = select_python_version(python_version_str)

            conda_dependencies = list(
                set(
                    [f"python={python_version}"]
                    + [dep for dep in self._base_conda_dependencies if "python" not in dep]
                    + [dep for dep in conda_dependencies if "python" not in dep]
                )
            )

            with temp_conda_env(self._tmp_directory, "tmp_env") as prefix:
                _, conda_pkg_reps = self._resolve_conda_dependencies(
                    prefix, platform, channels, conda_dependencies
                )
                transaction = None

        # we are checking deps against active conda env
        else:
            logger.info(
                "Using conda channels %s to install dependencies.", ", ".join(channels)
            )
            conda_dependencies = list(
            set(
                [dep for dep in self._base_conda_dependencies if "python" not in dep]
                + [dep for dep in conda_dependencies if "python" not in dep]
            )
            )
            transaction, conda_pkg_reps = self._resolve_conda_dependencies(
                    prefix, platform, channels, conda_dependencies
                )


        # return
        return {
            "pip": pip_dependencies,
            "conda": conda_pkg_reps,
            "python_version": python_version,
            "conda_transaction": transaction
        }

    def _resolve_conda_dependencies(
        self, prefix: str, platform: Literal["linux-64", "linux-32", "osx-64", "win-32", "win-64"], channels: List[str], conda_dependencies: List[str]
    ) -> List[dict]:
        """Resolves conda dependencies for an environment specification using mamba and
        formats a list of specs that can be used for installation.

        Args:
            prefix (str): Prefix of conda environment within which to resolve deps.
            platform (Literal["linux-64", "linux-32", "osx-64", "win-32", "win-64"]):
            conda-build platform target, see: https://docs.conda.io/projects/conda-build/en/latest/user-guide/tutorials/build-pkgs.html#converting-a-package-for-use-on-all-platforms
            channels (List[str]): List of channels for fetching packages.
            conda_dependencies (List[str]): List of conda dependencies to resolve.

        Returns:
            List[dict]: List of package representations in form:
                {"url": ..., "name":..., "filename": ...}

        Raises:
            NoPackagesToInstallError: MambaSolver did not return conda dependencies
                to install.

        """
        logger.info("Resolving conda dependencies...")

        to_install = None

        pkg_reps = []
        prefix = pathlib.Path(prefix)

        # create conda enviroment directories
        (prefix / "conda-meta").mkdir(parents=True, exist_ok=True)
        (prefix / "pkgs").mkdir(parents=True, exist_ok=True)

        libmamba_context = libmambapy.Context()
        libmamba_context.target_prefix = str(prefix)
        libmamba_context.pkgs_dirs = [str(prefix / "pkgs")]

        mamba_solver = MambaSolver(
            channels,
            platform,
            libmamba_context,
            output_folder=self._local_conda_channel_directory,
        )

        transaction = mamba_solver.solve(conda_dependencies)
        _, to_install, _ = transaction.to_conda()

        if to_install is None:
            logger.error("No packages found for installation.")
            raise NoPackagesToInstallError(channels, platform, conda_dependencies)

        # format specs
        else:
            for spec in to_install:
                rep = json.loads(spec[2])
                url = rep["url"]
                subdir = rep["subdir"]  # platform
                filename = rep["fn"]
                name = rep["name"]
                version = rep["version"]

                pkg_reps.append(
                    {"url": url, "subdir": subdir, "filename": filename, "name": name, "version": version}
                )

        return transaction, pkg_reps


    def _install_conda_dependencies_to_local_channel(
        self,
        conda_pkg_reps: List[dict],
        continue_on_fail: bool = False,
        rollback: bool = True,
    ) -> None:
        """Install conda dependencies to the local channel.

        Args:
            conda_pkg_reps (List[dict]): List of package representations in form:
                {"url": ..., "subdir":..., "filename": ..., "name": ...}
            continue_on_fail (bool): Whether to continue installation if a file cannot
                be downloaded.
            rollback (bool): Whether to remove all installed packages on installation
                fail.

        Returns:
            List[dict]: List of dictionary reps of the installation of the form:
                {"name": ..., "path": ..., "version": ...}

        """
        count = 1
        failed = []
        installed = []
        for rep in conda_pkg_reps:
            url = rep["url"]
            subdir = rep["subdir"]  # subdirs organized by platform
            filename = rep["filename"]
            name = rep["name"]
            version = rep["version"]


            # if the url is already a member of the local channel, skip
            if self._local_conda_channel_directory in url:
                logger.info(
                    "Skipping installation of %s, already installed at %s", name, url
                )
                continue

            file_target = f"{self._local_conda_channel_directory}/{subdir}/{filename}"
            success = False
            while count <= self._url_retry_count:
                logger.info("Collecting %s", file_target)
                try:
                    count += 1
                    urllib.request.urlretrieve(
                        url,
                        filename=file_target,
                    )
                    success = True
                    installed.append({"name": name, "path": file_target, "version": version})
                    break
                except Exception as e:
                    logger.error(
                        "Unable to retrieve %s with error: %s. Will attempt %s more \
                            tries.",
                        url,
                        e,
                        self._url_retry_count - count,
                    )

            if not success:
                logger.error("Unable to download %s while resolving dependencies.", url)
                failed.append(name)
                if not continue_on_fail:
                    break

        if not continue_on_fail and len(failed):
            logger.info("Some dependencies could not be installed with conda.")

            # remove all installed if rolling back
            if rollback:
                logger.info("Rolling back installed packages...")
                for pkg in installed:
                    logger.debug("Removing %s", pkg)
                    os.remove(pkg["path"])

                logger.info("Completed rollback.")

            raise UnableToInstallCondaDependenciesError(failed)

        return installed

    
    def _install_pip_dependencies_to_local_repo(
        self, pip_dependencies: List[str], python_version: str, platform: Literal["linux-64", "linux-32", "osx-64", "win-32", "win-64"]
    ) -> List[dict]:
        """Install required pip packages.

        Args:
            pip_dependencies (List[str]): List of string python dependencies to install
            python_version (str): Version of python to use for installation
            platform (Literal["linux-64", "linux-32", "osx-64", "win-32", "win-64"]):
            conda-build platform target, see: https://docs.conda.io/projects/conda-build/en/latest/user-guide/tutorials/build-pkgs.html#converting-a-package-for-use-on-all-platforms

        Returns:
            List[dict]: List of dictionary reps of the installation of the form:
                {"name": ..., "path": ..., "version": ...}

        Raises:
            UnableToInstallPipDependenciesError: Failed installation.

        """

        # must run as verbose to get the downloaded files
        pip_cmd = (
            [sys.executable, "-m", "pip", "download"]
            + pip_dependencies
            + [
                "--platform",
                platform,
                "--python-version",
                python_version,
                "--no-deps",
                "--exists-action",
                "i",
                "-d",
                self._local_pip_directory,
                "-v",
            ]
        )

        # run pip command
        full_filepaths = []
        try:
            download_proc = subprocess.check_output(
                pip_cmd
            )

            output_lines = download_proc.decode("utf-8").split("\n")
            package_lines = [
                line.replace("Saved ", "") for line in output_lines if "Saved " in line
            ]

            full_filepaths = [str(os.path.abspath(line)) for line in package_lines]
            logger.info("Pip files installed: %s", ", ".join(full_filepaths))

        except subprocess.CalledProcessError as e:
            raise UnableToInstallPipDependenciesError(
                pip_dependencies, python_version, platform, e
            )


        pip_deps = []
        # Now, we can get the metadata from the file
        for pkg_file in full_filepaths:
            pkg = SDist(pkg_file)
            version = pkg.version
            name = pkg.name

            pip_deps.append({"name": name, "version": version, "filename": pkg_file})

        return pip_deps


    def _index_local_conda_channel(self) -> None:
        """Indexes the local conda channel to register the downloaded packages.

        Raises:
            UnableToIndexLocalChannelError: Index subprocess did not exit successfully.

        """
        index_proc = subprocess.Popen(
            ["conda", "index", f"file://{self._local_conda_channel_directory}"],
            stdout=subprocess.PIPE,
        )
        output = index_proc.communicate()[0]
        return_code = index_proc.returncode

        if return_code != 0:
            logger.error(
                "Unable to index channel at %s", self._local_conda_channel_directory
            )
            raise UnableToIndexLocalChannelError(
                self._local_conda_channel_directory, return_code, output
            )

