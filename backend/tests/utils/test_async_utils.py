
import asyncio
import pytest
from src.utils.async_utils import run_async

async def sample_coroutine():
    await asyncio.sleep(0.01)
    return "done"

@pytest.mark.asyncio
async def test_run_async_with_running_loop():
    # This test runs within the pytest-asyncio event loop
    task = run_async(sample_coroutine())
    assert isinstance(task, asyncio.Task)
    result = await task
    assert result == "done"

def test_run_async_without_running_loop():
    # This test runs outside of an asyncio event loop
    result = run_async(sample_coroutine())
    assert result == "done"
