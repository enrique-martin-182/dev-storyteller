import asyncio
import pytest
from unittest.mock import MagicMock, patch

from src.utils.async_utils import run_async

@pytest.mark.asyncio
async def test_run_async_no_running_loop():
    """
    Test run_async when no event loop is currently running.
    """
    mock_coro = MagicMock(name="mock_coroutine")
    mock_coro.return_value = "coro_result"

    with patch("src.utils.async_utils.asyncio.get_running_loop", side_effect=RuntimeError) as mock_get_running_loop, \
         patch("src.utils.async_utils.asyncio.run") as mock_asyncio_run:

        mock_asyncio_run.return_value = "coro_result"

        result = run_async(mock_coro)

        mock_get_running_loop.assert_called_once()
        mock_asyncio_run.assert_called_once_with(mock_coro)
        assert result == "coro_result"

@pytest.mark.asyncio
async def test_run_async_with_running_loop():
    """
    Test run_async when an event loop is already running.
    """
    mock_coro = MagicMock(name="mock_coroutine")
    mock_coro.return_value = "coro_result"

    mock_running_loop = MagicMock()
    mock_running_loop.is_running.return_value = True
    mock_running_loop.create_task.return_value = "task_object" # asyncio.create_task returns a Task object

    with patch("src.utils.async_utils.asyncio.get_running_loop", return_value=mock_running_loop) as mock_get_running_loop, \
         patch("src.utils.async_utils.asyncio.run") as mock_asyncio_run:

        result = run_async(mock_coro)

        mock_get_running_loop.assert_called_once()
        mock_running_loop.is_running.assert_called_once()
        mock_running_loop.create_task.assert_called_once_with(mock_coro)
        mock_asyncio_run.assert_not_called()
        assert result == "task_object"

@pytest.mark.asyncio
async def test_run_async_loop_not_running():
    """
    Test run_async when a loop exists but is not running.
    """
    mock_coro = MagicMock(name="mock_coroutine")
    mock_coro.return_value = "coro_result"

    mock_existing_loop = MagicMock()
    mock_existing_loop.is_running.return_value = False

    with patch("src.utils.async_utils.asyncio.get_running_loop", return_value=mock_existing_loop) as mock_get_running_loop, \
         patch("src.utils.async_utils.asyncio.run") as mock_asyncio_run:

        mock_asyncio_run.return_value = "coro_result"

        result = run_async(mock_coro)

        mock_get_running_loop.assert_called_once()
        mock_existing_loop.is_running.assert_called_once()
        mock_asyncio_run.assert_called_once_with(mock_coro)
        mock_existing_loop.create_task.assert_not_called()
        assert result == "coro_result"