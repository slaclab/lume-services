import os
from pydantic import ValidationError
import pytest
import docker
from docker.errors import DockerException
from prefect.run_configs import LocalRun, DockerRun, KubernetesRun
from lume_services.services.scheduling.backends.kubernetes import (
    KubernetesBackend,
    KubernetesRunConfig,
)
from lume_services.services.scheduling.backends.docker import (
    DockerBackend,
    DockerRunConfig,
)

from lume_services.services.scheduling.backends.local import (
    LocalBackend,
    LocalRunConfig,
)

import logging

logger = logging.getLogger(__name__)

# from lume_services.tests.fixtures.services.models import *  # noqa: F403, F401
# from lume_services.tests.fixtures.services.scheduling import *  # noqa: F403, F401


@pytest.fixture(scope="session", autouse=True)
def docker_api_version():
    client = docker.from_env()
    return client.api.version()["ApiVersion"]


class TestRunConfigs:
    labels = ["test"]
    env = dict(os.environ)
    image = "placeholder_image_tag"
    docker_api_version_min = "1.35"  # lowest allowed
    docker_api_version_latest = "1.41"  # latest tested

    docker_host_config = {
        "cpu_quota": 2,
        "cpu_period": 1999,
        "blkio_weight": 1999,
        "blkio_weight_device": [{"Path": "/dev/sda", "Rate": 1000}],
        "device_read_bps": [{"Path": "/dev/sda", "Rate": 1000}],
        "device_write_bps": [{"Path": "/dev/sda", "Rate": 1000}],
        "device_read_iops": [{"Path": "/dev/sda", "Rate": 1000}],
        "device_write_iops": [{"Path": "/dev/sda", "Rate": 1000}],
        "shm_size": 67108864,
        "oom_kill_disable": True,
        "userns_mode": "host",
        "oom_score_adj": 100,
        "dns_opt": ["use-vc", "no-tld-query"],
        "mem_reservation": "67108864",
        "kernel_memory": 67108864,
        "pids_limit": 1024,
        "isolation": "hyperv",
        "pid_mode": "host",
        "mem_swappiness": 40,
        "volume_driver": "local",
        "cpu_count": 2,
        "cpu_percent": 15,
        "nano_cpus": 1000,
        "cpu_rt_period": 100,
        "cpu_rt_runtime": 1000,
    }
    # from https://github.com/docker/docker-py/blob/a48a5a9647761406d66e8271f19fab7fa0c5f582/tests/unit/dockertypes_test.py#L15 # noqa
    broken_docker_host_config = {
        "shm_size": ["test"],
        "mem_reservation": ["test"],
        "kernel_memory": ["test"],
        "cpu_count": ["1"],
        "cpu_percent": ["test"],
        "nano_cpus": "0",
        "cpu_rt_period": "1000",
        "cpu_rt_runtime": "1000",
    }
    docker_ports = [3000]

    def test_local_run_config(self):
        # check construction
        run_config = LocalRunConfig(labels=self.labels, env=self.env)

        # check that the working_dir is the same as pytest workdir
        assert run_config.working_dir == str(os.getcwd())
        # check env assignment
        assert run_config.env == self.env
        # check label assignment
        assert all([label in run_config.labels for label in self.labels])
        # check build of prefect run config
        prefect_run_config = run_config.build()
        assert isinstance(prefect_run_config, (LocalRun,))
        assert all([label in prefect_run_config.labels for label in run_config.labels])
        assert prefect_run_config.env == run_config.env
        assert prefect_run_config.working_dir == run_config.working_dir

    def test_docker_run_config(self, docker_api_version):
        self.docker_host_config["version"] = docker_api_version
        # check construction missing image
        with pytest.raises(ValidationError):
            DockerRunConfig(
                labels=self.labels,
                env=self.env,
                ports=self.docker_ports,
                host_config=self.docker_host_config,
            )

        # check w/ auto version
        try:
            run_config = DockerRunConfig(
                labels=self.labels,
                env=self.env,
                image=self.image,
                ports=self.docker_ports,
                host_config=self.docker_host_config,
            )
        except Exception as e:
            logger.error("Error using api version %s", docker_api_version)
            raise e

    def test_docker_run_config_latest_api(self):

        # check failure on faulty values
        for key, values in self.broken_docker_host_config.items():
            for value in values:
                with pytest.raises((ValidationError, DockerException)):
                    try:
                        # test latest version
                        DockerRunConfig(
                            labels=self.labels,
                            image=self.image,
                            env=self.env,
                            ports=self.docker_ports,
                            host_config={
                                "version": self.docker_api_version_latest,
                                key: value,
                            },
                        )
                        logger.error(
                            "Error Testing docker run config w/ latest version for %s = %s",
                            key,
                            value,
                        )
                    except ValidationError as err:
                        logger.error(
                            "Error Testing docker run config w/ latest version for %s = %s",
                            key,
                            value,
                        )
                        raise err

    def test_docker_run_config_min_api(self):
        # check failure on faulty values
        for key, values in self.broken_docker_host_config.items():
            for value in values:
                with pytest.raises((ValidationError, DockerException)):
                    # test min version
                    try:
                        # test latest version
                        DockerRunConfig(
                            labels=self.labels,
                            image=self.image,
                            env=self.env,
                            ports=self.docker_ports,
                            host_config={
                                "version": self.docker_api_version_min,
                                key: value,
                            },
                        )
                    except ValidationError as err:
                        logger.error(
                            "Error Testing docker run config w/ min version for %s = %s",
                            key,
                            value,
                        )
                        raise err

    @pytest.mark.skip()
    def test_kubernetes_run_config(self):

        ...

        # packaged yaml should be applied in case of missing job template and path


@pytest.mark.skip()
class TestLocalBackend:
    ...


@pytest.mark.skip()
class TestDockerBackend:
    def test_docker_config_construction(self, file_service):

        mounted_filesystems = file_service.get_mounted_filesystems()
        mounts = []
        for filesystem in mounted_filesystems.values():
            mounts.append(
                {
                    "target": filesystem.mount_alias,
                    "source": filesystem.mount_path,
                    "type": "bind",
                }
            )

        host_config = DockerHostConfig(
            mounts=mounts, resource_request={"cpu_shares": 1, "cpuset_cpus": 2}
        )

        DockerRunConfig(image="test", env={}, host_config=host_config)

    def test_init_backend(self, docker_run_config):
        _ = DockerBackend(**docker_run_config)


@pytest.mark.skip()
class TestKubernetesBackend:
    def test_init_backend(self):
        test_dict = {
            "job_template": {
                "filepath": "my_filepath",
                "filesystem_identifier": "local",
            },
            "image_pull_policy": "Always",
            "default_image": "my_test_image",
        }

        backend = KubernetesBackend(**test_dict)

        assert backend.job_template.filepath == "my_filepath"
        assert backend.job_template.filesystem_identifier == "local"
        assert backend.image_pull_policy == "Always"
        assert backend.default_image == "my_test_image"

    def test_init_resource_request(self):
        test_dict = {
            "cpu": {"limit": 1.0, "request": 0.5},
            "memory": {
                "limit": "10MiB",
                "request": "10MiB",
            },
        }

        resource_request = KubernetesResourceRequest(**test_dict)

        assert resource_request.cpu.limit == 1.0
        assert resource_request.cpu.request == 0.5
        assert resource_request.memory.limit == "10MiB"
        assert resource_request.memory.request == "10MiB"
