import pytest
from datetime import datetime

from lume_services.context import Context, LUMEServicesConfig


@pytest.fixture(scope="module")
def context(
    mongodb_service,
    mysql_service,
    mysql_config,
    mongodb_config,
    file_service,
):
    # don't use factory here because want to use pytest fixture management
    config = LUMEServicesConfig(
        model_db_service_config=mysql_config,
        results_db_service_config=mongodb_config,
    )

    context = Context(
        results_db_service=mongodb_service,
        model_db_service=mysql_service,
        file_service=file_service,
    )

    context.config.from_pydantic(config)

    return context


@pytest.fixture(scope="session", autouse=True)
def test_generic_result_document():
    return {
        "flow_id": "test_flow_id",
        "inputs": {"input1": 2.0, "input2": [1, 2, 3, 4, 5], "input3": "my_file.txt"},
        "outputs": {
            "output1": 2.0,
            "output2": [1, 2, 3, 4, 5],
            "ouptut3": "my_file.txt",
        },
    }


@pytest.fixture(scope="module", autouse=True)
def test_impact_result_document():
    return {
        "flow_id": "test_flow_id",
        "inputs": {"input1": 2.0, "input2": [1, 2, 3, 4, 5], "input3": "my_file.txt"},
        "outputs": {
            "output1": 2.0,
            "output2": [1, 2, 3, 4, 5],
            "ouptut3": "my_file.txt",
        },
        "plot_file": "my_plot_file.txt",
        "archive": "archive_file.txt",
        "pv_collection_isotime": datetime.now(),
        "config": {"config1": 1, "config2": 2},
    }
