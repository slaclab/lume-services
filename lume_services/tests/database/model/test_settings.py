from lume_services.database.model.db import Flow, Project, Deployment, Model
import pytest

sample_model = {
    "author": "Jackie Garrahan",
    "laboratory": "slac",
    "facility": "lcls",
    "beampath": "cu_hxr",
    "description": "test model"
}

sample_deployment= {
    "version": "v0.0",
    "sha256": "placeholder",
    "url": "http://mytest.com",
    "package-name": "test_package",
    "asset_dir": None, # opt
    "asset_url": None, # opt
    "deployment_id": "0",
}

sample_project = {
    "project_name": "my_project",
    "description": "placeholder",
}

sample_flow = {
    "flow_id": "0",
    "deployment_ids": [0],
    "flow_name": "my_test_flow",
    "project_name": "my_projcet",
}


@pytest.mark.skip
def test_model_settings(settings):

    model = Model(**settings)

    """
    with raise ...:
        # add misc key not in
        settings["misc_key"] = "dummy"

        model = Model(**settings)
    """

""""
def test_deployment_settings(settings):

    deployment = Deployment(**settings)


    with raise ...:
        # add misc key not in
        settings["misc_key"] = "dummy"

        deployment = Deployment(**settings)


def test_flow_settings(settings):

    flow = Flow(**settings)


    with raise ...:
        # add misc key not in
        settings["misc_key"] = "dummy"

        flow = Flow(**settings)


def test_project_settings(settings):

    project = Project(**settings)


    with raise ...:
        # add misc key not in
        settings["misc_key"] = "dummy"

        project = Project(**settings)
"""