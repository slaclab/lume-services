from lume_services.scheduling.prefect.backends.kubernetes import (
    KubernetesBackend,
    KubernetesResourceRequest,
)


# MISSING TESTS:
# test incorrect type assignment


def test_init_backend_by_dict():

    test_dict = {
        "job_template": {"filepath": "my_filepath", "filesystem_identifier": "local"},
        "image_pull_policy": "Always",
        "default_image": "my_test_image",
    }

    backend = KubernetesBackend(**test_dict)

    assert backend.job_template.filepath == "my_filepath"
    assert backend.job_template.filesystem_identifier == "local"
    assert backend.image_pull_policy == "Always"
    assert backend.default_image == "my_test_image"


def test_init_resource_request():

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
