

# Path: tests/conftest.py

import pytest

import os

from vcg.videogen.bgm import BGM


@pytest.fixture(scope='session', autouse=True)
def BGM_instance():
  workspace = os.path.dirname(__file__)
  path = os.path.join(workspace, 'data', 'bgm')
  os.environ['VCG_BGM_ROOT'] = path
  return BGM()
