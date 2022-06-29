from lume_services.services.scheduling.tasks import (
    load_db_result_task,
    save_db_result_task,
    load_file_task,
    save_file_task,
)
from lume_services.tests.files import SAMPLE_TEXT_FILE
from lume_services.data.files import TextFile
from prefect import Flow, task


class TestDBTaskResults:
    def test_save_db_result_task(self, results_db_service, generic_result):

        with Flow("save_db_result_task_flow") as flow:
            my_task = save_db_result_task(
                generic_result, results_db_service=results_db_service
            )

        flow_run = flow.run()

        assert flow_run.is_successful()
        assert flow_run.result[my_task].is_successful()
        assert flow_run.result[my_task].result == generic_result.unique_rep()

    def test_load_db_result_task(self, results_db_service, generic_result):

        result_rep = generic_result.unique_rep()

        with Flow("load_db_result_task_flow") as flow:
            my_task = load_db_result_task(
                result_rep, results_db_service=results_db_service
            )

        flow_run = flow.run()

        assert flow_run.is_successful()
        assert flow_run.result[my_task].is_successful()
        assert flow_run.result[my_task].result == generic_result

    def test_db_result_propogation(self, results_db_service, generic_result):

        result_rep = generic_result.unique_rep()

        @task
        def return_result(result):
            return result

        with Flow("load_db_result_task_flow") as flow:
            my_task = load_db_result_task(
                result_rep, results_db_service=results_db_service
            )
            downstream_task = return_result(my_task)

        flow_run = flow.run()

        assert flow_run.is_successful()
        assert flow_run.result[my_task].is_successful()
        assert flow_run.result[downstream_task].is_successful()
        assert flow_run.result[downstream_task].result == generic_result


class TestFileTaskResults:
    def test_save_file_task(self, tmp_path, file_service):

        filepath = f"{tmp_path}/tmp_file.txt"
        text = "text"
        text_file = TextFile(
            obj=text, filename=filepath, file_system_identifier="local"
        )

        with Flow("save_file_task_flow") as flow:
            my_task = save_file_task(
                obj=text,
                file_type=TextFile,
                filename=filepath,
                file_system_identifier="local",
                file_service=file_service,
            )

        flow_run = flow.run()
        assert flow_run.is_successful()
        assert flow_run.result[my_task].is_successful()
        assert flow_run.result[my_task].result == text_file.jsonable_dict()

    def test_load_file_task(self, file_service):

        text_file = TextFile(filename=SAMPLE_TEXT_FILE, file_system_identifier="local")
        text_file_rep = text_file.jsonable_dict()

        with Flow("load_file_task_flow") as flow:
            my_task = load_file_task(text_file_rep, file_service=file_service)

        flow_run = flow.run()
        assert flow_run.is_successful()
        assert flow_run.result[my_task].is_successful()
        assert flow_run.result[my_task].result == text_file.read(
            file_service=file_service
        )

    def test_file_result_propogation(self, file_service):

        text_file = TextFile(filename=SAMPLE_TEXT_FILE, file_system_identifier="local")
        text_file_rep = text_file.jsonable_dict()

        # @task
        def return_text(text):
            return text

        with Flow("load_file_task_flow") as flow:
            my_task = load_file_task(text_file_rep, file_service=file_service)
            downstream_task = return_text(my_task)

        flow_run = flow.run()
        assert flow_run.is_successful()
        assert flow_run.result[my_task].is_successful()
        assert flow_run.result[downstream_task].is_successful()
        assert flow_run.result[downstream_task].result == text_file.read(
            file_service=file_service
        )
