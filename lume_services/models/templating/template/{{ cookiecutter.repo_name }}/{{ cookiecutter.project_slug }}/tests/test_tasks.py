import pytest

from my_prefect_collection.tasks import my_task


async def test_successful_task(mock_successful_calls):
    my_task_result = await my_task.fn()

    assert type(trigger_sync_result) is whatever
