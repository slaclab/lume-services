from datetime import datetime
import pytest
from PIL import Image
from lume_services.data.results import (
    GenericResult,
    ImpactResult,
    get_result_from_string,
)
from lume_services.tests.files import SAMPLE_IMPACT_ARCHIVE, SAMPLE_IMAGE_FILE


@pytest.mark.parametrize(
    ("string", "result_class_target"),
    [
        ("lume_services.data.results.generic:GenericResult", GenericResult),
        ("lume_services.data.results.impact:ImpactResult", ImpactResult),
        pytest.param(
            "incorrect.import.string",
            GenericResult,
            marks=pytest.mark.xfail(strict=True),
        ),
    ],
)
def test_get_result_from_string(string, result_class_target):
    result_type = get_result_from_string(string)
    assert result_type == result_class_target


def test_create_generic_result():
    generic_result = GenericResult(
        collection="generic",
        flow_id="test_flow_id",
        inputs={"input1": 4, "input2": 3},
        outputs={"output1": 1},
    )

    generic_result.json()


class TestImpactResult:
    @pytest.fixture
    def impact_result(self):
        """Impact result fixture"""
        return ImpactResult(
            collection="generic",
            flow_id="test_flow_id",
            inputs={"input1": 4, "input2": 3},
            outputs={"output1": 1},
            archive={
                "filename": SAMPLE_IMPACT_ARCHIVE,
                "file_system_identifier": "local",
            },
            plot_file={
                "filename": SAMPLE_IMAGE_FILE,
                "file_system_identifier": "local",
            },
            pv_collection_isotime=datetime.utcnow(),
            config={"example_config": 1},
        )

    def test_to_json(self, impact_result):
        impact_result.json()

    def test_from_json(self, impact_result):
        json_rep = impact_result.json()
        impact_result.parse_raw(json_rep)

    def test_load_image(self, impact_result, context):
        image = impact_result.plot_file.read(context.file_service())
        assert isinstance(image, (Image.Image,))
