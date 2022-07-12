from lume_services.services.scheduling.backends.kubernetes import (
    KubernetesBackend,
    KubernetesResourceRequest,
)
from lume_services.services.scheduling.backends.docker import (
    DockerBackend,
    DockerRunConfig,
    DockerHostConfig,
)


from lume_services.tests.fixtures.services.models import *  # noqa: F403, F401
from lume_services.tests.fixtures.services.scheduling import *  # noqa: F403, F401


class TestLocalBackend:
    ...


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
