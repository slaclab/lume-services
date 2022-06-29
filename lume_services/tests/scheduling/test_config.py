import prefect
from lume_services.scheduling.prefect.config import PrefectConfig
from lume_services.scheduling.prefect.backends import KubernetesBackend


class test_prefect_config:

    config = PrefectConfig(
        backend=KubernetesBackend(),
        api="http://localhost:4100",
        graphql="http://localhost:4100/graphql",
        ui="http://localhost:8081",
    )
    config.apply()

    # check assignment
    assert isinstance(prefect.config.backend, (KubernetesBackend,))
    assert prefect.config.cloud.api == "http://localhost:4100"
    assert prefect.config.cloud.graphql == "http://localhost:4100/graphql"
    assert prefect.config.server.ui.endpoint == "http://localhost:8081"
