import os
import json
import urllib
import subprocess
from contextlib import contextmanager
from mamba.api import MambaSolver
import libmambapy
from pydantic import BaseModel
from typing import List
import pathlib
from typing import Optional, Literal

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
)

import logging

logger = logging.getLogger(__name__)


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
        raise EnvironmentFileNotFound

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
        local_pip_directory (str):
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

    """  # noqa

    local_pip_directory: str
    local_conda_channel_directory: str
    base_env_filepath: Optional[str] = ENVIRONMENT_YAML
    tmp_directory: str = "/tmp/lume-services"
    platform: Literal["linux-64", "linux-32", "osx-64", "win-32", "win-64"] = "linux-64"
    url_retry_count: int = 3


class EnvironmentResolver:
    """
    Must be run by a user that has read/write permissions to the local channel path and
    tmp_path

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
        self._base_channels = []
        self._base_conda_dependencies = []
        self._base_pip_dependencies = []
        self._platform = config.platform
        self._local_conda_channel_directory = config.local_conda_channel_directory
        self._local_pip_directory = config.local_pip_directory
        self._base_env_filepath = config.base_env_filepath
        self._tmp_directory = config.tmp_directory
        self._url_retry_count = config.url_retry_count

        if config.base_env_filepath is not None:
            # check existence of file
            if not os.path.isfile(self._base_env_filepath):
                raise EnvironmentFileNotFound(self._base_env_filepath)

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

    def run(
        self,
        environment_yaml_path: str,
        continue_on_fail: bool = False,
        rollback: bool = True,
    ) -> None:
        """Solve environment and install dependencies to local channels.

        Args:
            environment_yaml_path (str): String path to the environment YAML.
            continue_on_fail (bool): Whether to continue installation if a file cannot
                be downloaded.
            rollback (bool): Whether to remove all installed packages on installation
                fail.

        """
        channels, conda_dependencies, pip_dependencies = load_environment_yaml(
            environment_yaml_path
        )

        channels = list(set(self._base_channels + channels))

        # filter python dependency
        conda_dependencies = list(
            set(
                [dep for dep in conda_dependencies if "python" not in dep]
                + self._base_conda_dependencies
            )
        )

        # build pip dependencies
        pip_dependencies = list(set(self._base_pip_dependencies + pip_dependencies))

        conda_pkg_reps = self._resolve_conda_dependencies(channels, conda_dependencies)
        self._install_conda_dependencies_to_local_channel(
            conda_pkg_reps, continue_on_fail=continue_on_fail, rollback=rollback
        )

    def _resolve_conda_dependencies(
        self, channels: List[str], conda_dependencies: List[str]
    ) -> List[dict]:
        """Resolves conda dependencies for an environment specification using mamba and
        formats a list of specs that can be used for installation.

        Args:
            channels (List[str]): List of channels for fetching packages.
            conda_dependencies (List[str]): List of conda dependencies to resolve.

        Returns:
            List[dict]: List of package representations in form:
                {"url": ..., "subdir":..., "filename": ...}

        Raises:
            NoPackagesToInstallError: MambaSolver did not return conda dependencies
                to install.

        """

        to_install = None

        pkg_reps = []
        # create a temporary environment to resolve deps against
        with temp_conda_env(self._tmp_directory, "tmp_env") as prefix:
            prefix = pathlib.Path(prefix)

            # create conda enviroment directories
            (prefix / "conda-meta").mkdir(parents=True, exist_ok=True)
            (prefix / "pkgs").mkdir(parents=True, exist_ok=True)

            libmamba_context = libmambapy.Context()
            libmamba_context.target_prefix = str(prefix)
            libmamba_context.pkgs_dirs = [str(prefix / "pkgs")]

            mamba_solver = MambaSolver(
                channels,
                self._platform,
                libmamba_context,
                output_folder=self._local_conda_channel_directory,
            )

            transaction = mamba_solver.solve(conda_dependencies)
            _, to_install, _ = transaction.to_conda()

        if to_install is None:
            raise NoPackagesToInstallError(channels, self._platform, conda_dependencies)

        # format specs
        else:
            for spec in to_install:
                rep = json.loads(spec[2])
                url = rep["url"]
                subdir = rep["subdir"]  # platform
                filename = rep["fn"]
                name = rep["name"]

                pkg_reps.append(
                    {"url": url, "subdir": subdir, "filename": filename, "name": name}
                )

        return pkg_reps

    def _install_conda_dependencies_to_local_channel(
        self,
        conda_pkg_reps: List[dict],
        continue_on_fail: bool = False,
        rollback: bool = True,
    ) -> None:
        """Install conda dependencies to the local channel.

        Args:
            conda_pkg_reps (List[dict]): List of package representations in form:
                {"url": ..., "subdir":..., "filename": ...}
            continue_on_fail (bool): Whether to continue installation if a file cannot
                be downloaded.
            rollback (bool): Whether to remove all installed packages on installation
                fail.

        """
        count = 1
        failed = []
        installed = []
        for rep in conda_pkg_reps:
            url = rep["url"]
            subdir = rep["subdir"]  # platform
            filename = rep["filename"]
            name = rep["name"]

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
                    installed.append(file_target)
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

            installed.append(file_target)

        if not continue_on_fail:
            logger.info("Some dependencies could not be installed with conda.")

            # remove all installed if rolling back
            if rollback:
                logger.info("Rolling back installed packages...")
                for pkg in installed:
                    logger.debug("Removing %s", pkg)
                    os.remove(pkg)

                logger.info("Completed rollback.")

            raise UnableToInstallCondaDependenciesError(failed)

    def _install_pip_dependencies_to_local_repo(self, pip_dependencies) -> None:
        ...

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


if __name__ == "__main__":
    config = EnvironmentResolverConfig(
        local_pip_directory="/Users/jgarra/sandbox/lume-services/dev/pip",
        local_conda_channel_directory="/Users/jgarra/sandbox/lume-services/dev/local-channel",
    )

    resolver = EnvironmentResolver(config)

    resolver.run("/Users/jgarra/sandbox/lume-services/simple_env.yml")
