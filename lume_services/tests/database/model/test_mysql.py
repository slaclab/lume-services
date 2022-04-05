import pytest

@pytest.fixture(scope="module", autouse=True)
def model_dict():
    return {
        "author": "Jackie Garrahan",
        "laboratory": "slac",
        "facility": "lcls",
        "beampath": "cu_hxr",
        "description": "test model"
    }

@pytest.fixture(scope="module", autouse=True)
def deployment_dict():
    return {
        "version": "v0.0",
        "sha256": "placeholder",
        "url": "http://mytest.com",
        "package_name": "test_package",
        "asset_dir": None, # opt
        "asset_url": None, # opt
        "deployment_id": "0",
    }

@pytest.fixture(scope="module", autouse=True)
def project_dict():
    return {
        "project_name": "my_project",
        "description": "placeholder",
    }

@pytest.fixture(scope="module", autouse=True)
def flow_dict():
    return {
        "flow_id": "0",
        "deployment_ids": [0],
        "flow_name": "my_test_flow",
        "project_name": "my_projcet",
    }

@pytest.fixture(scope="module", autouse=True)
def test_store_model(model_db_service, model_dict):

    model_id = model_db_service.store_model(**model_dict)
    assert model_id is not None

    return model_id

def test_get_model(model_db_service, test_store_model):

    model = model_db_service.get_model(model_id=test_store_model)

    assert model.model_id == test_store_model



@pytest.fixture(scope="module", autouse=True)
def test_store_deployment(model_db_service, deployment_dict, test_store_model):

    deployment_dict["model_id"] = test_store_model
    deployment_id = model_db_service.store_deployment(**deployment_dict)

    assert deployment_id is not None

    return deployment_id


@pytest.fixture(scope="module", autouse=True)
def test_store_project(model_db_service, project_dict):

    return model_db_service.store_project(**project_dict)


@pytest.fixture(scope="module", autouse=True)
def test_store_flow(model_db_service, flow_dict, test_store_deployment, test_store_project):

    flow_dict["project_name"] = test_store_project

    flow_dict["deployment_ids"] = test_store_deployment
    flow_id = model_db_service.store_flow(**flow_dict)

    return flow_id

"""

@pytest.mark.skip
def test_get_deployment(model_db_service, test_store_deployment):

    deployment = model_db_service.get_deployment(**test_store_deployment.dict())

    assert deployment.deployment_id == test_store_deployment.deployment_id

@pytest.mark.skip
def test_get_latest_deployment(model_db_service, test_store_model):

    deployment = model_db_service.get_latest_deployment(model_id=test_store_model.model_id)

    assert deployment.deployment_id == test_store_deployment.deployment_id

@pytest.mark.skip
def test_get_project(model_db_service, test_store_project):

    project = model_db_service.get_project(**test_store_project.dict())

    assert project.project_name == test_store_project.project_name

@pytest.mark.skip
def test_get_flow(model_db_service, test_store_flow):

    flow = model_db_service.get_flow(**test_store_flow.dict())

    assert flow.flow_id == test_store_flow.flow_id

"""