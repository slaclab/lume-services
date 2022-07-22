import prefect
import pytest


def test_prefect_config(prefect_config):
    # check assignment, has already been applied
    assert prefect.config.debug == prefect_config.debug
    assert prefect.config.home_dir == prefect_config.home_dir

    # check server values
    for key, value in prefect_config.server.dict().items():
        attr = getattr(prefect.config.server, key)
        assert attr == value

    # check graphql values
    for key, value in prefect_config.graphql.dict().items():
        attr = getattr(prefect.config.server.graphql, key)
        assert attr == value

    # check hasura values
    for key, value in prefect_config.hasura.dict().items():
        attr = getattr(prefect.config.server.hasura, key)
        assert attr == value

    # check ui values
    for key, value in prefect_config.ui.dict().items():
        attr = getattr(prefect.config.server.ui, key)
        assert attr == value

    # check graphql values
    for key, value in prefect_config.telemetry.dict().items():
        attr = getattr(prefect.config.server.telemetry, key)
        assert attr == value


def test_prefect_update_config(prefect_config):

    new_config = prefect_config.copy()
    new_config.server.host = "0.0.0.0"
    new_config.server.host_port = 4000
    new_config.graphql.host = "0.0.0.0"
    new_config.graphql.host_port = 4000
    new_config.hasura.host = "0.0.0.0"
    new_config.hasura.host_port = 4000
    new_config.postgres.host = "0.0.0.0"
    new_config.postgres.host_port = 4000
    new_config.postgres.db = "placeholder"
    new_config.postgres.user = "placeholder"
    new_config.postgres.password = "placeholder"
    new_config.postgres.data_path = "placeholder"

    new_config.apply()

    # check server values
    for key, value in prefect_config.server.dict().items():
        attr = getattr(prefect.config.server, key)
        assert attr == value

    # check graphql values
    for key, value in prefect_config.graphql.dict().items():
        attr = getattr(prefect.config.server.graphql, key)
        assert attr == value

    # check hasura values
    for key, value in prefect_config.hasura.dict().items():
        attr = getattr(prefect.config.server.hasura, key)
        assert attr == value

    # check ui values
    for key, value in prefect_config.ui.dict().items():
        attr = getattr(prefect.config.server.ui, key)
        assert attr == value

    # check graphql values
    for key, value in prefect_config.telemetry.dict().items():
        attr = getattr(prefect.config.server.telemetry, key)
        assert attr == value

    prefect_config.apply()


@pytest.mark.skip()
class TestSchedulingService:
    def test_init_service(self):
        ...

    def test_flow_of_flows_registration(self):
        ...
