import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.utils.async_utils import run_async


@pytest.mark.asyncio
async def test_run_async_no_running_loop():
    """
    Test run_async when no event loop is currently running.
    It should create and run a new loop.
    """
    mock_coro = AsyncMock(return_value="coroutine_result")

    with patch("asyncio.get_running_loop", side_effect=RuntimeError), \
         patch("asyncio.run") as mock_asyncio_run:

        mock_asyncio_run.return_value = "coroutine_result" # Set the return value for asyncio.run
        
        result = run_async(mock_coro)

        mock_asyncio_run.assert_called_once_with(mock_coro)
        assert result == "coroutine_result"


@pytest.mark.asyncio
async def test_run_async_with_running_loop():
    """
    Test run_async when an event loop is already running.
    It should create a task in the existing loop.
    """
    mock_coro = AsyncMock(return_value="coroutine_result")
    mock_task = MagicMock()
    
    mock_loop = MagicMock()
    mock_loop.is_running.return_value = True
    mock_loop.create_task.return_value = mock_task

    with patch("asyncio.get_running_loop", return_value=mock_loop), \
         patch("asyncio.run") as mock_asyncio_run:

        result = run_async(mock_coro)

        mock_loop.create_task.assert_called_once_with(mock_coro)
        mock_asyncio_run.assert_not_called()
        assert result == mock_task