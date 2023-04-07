# Path: tests/test_temporalflow.py

import pytest
import pytest_asyncio

import asyncio
import uuid
from typing import AsyncGenerator

from temporalio.client import Client
from temporalio.testing import WorkflowEnvironment
from temporalio.service import RetryConfig

from vcg.temporalflow import main


# temporal workflow testing
# https://github.com/temporalio/samples-python/blob/main/tests/conftest.py
# def pytest_addoption(parser):
#   parser.addoption(
#     "--workflow-environment",
#     default='time-skipping',
#     help="`local`, `time-skipping`, or target to existing server)",
#   )


@pytest.fixture(scope="session")
def event_loop():
  # See https://github.com/pytest-dev/pytest-asyncio/issues/68
  # See https://github.com/pytest-dev/pytest-asyncio/issues/257
  # Also need ProactorEventLoop on older versions of Python with Windows so
  # that asyncio subprocess works properly
  loop = asyncio.get_event_loop_policy().new_event_loop()
  yield loop
  loop.close()


@pytest_asyncio.fixture(scope="session")
async def env() -> AsyncGenerator[WorkflowEnvironment, None]:
  env = await WorkflowEnvironment.start_time_skipping(
    retry_config=RetryConfig(),
    test_server_existing_path='/Users/zhengt/Applications/temporalite_0.3.0_darwin_arm64/temporalite'
  )
  yield env
  await env.shutdown()


@pytest_asyncio.fixture
async def client(env: WorkflowEnvironment) -> Client:
  return env.client


@pytest.mark.skip
@pytest.mark.asyncio
async def test_main(client, params):
  task_queue = str(uuid.uuid4())

  yield main(client, task_queue)
  await client.execute_workflow(
    'VideoClipGen',
    params,
    id=str(uuid.uuid4()),
    task_queue=task_queue,
  )
