# Path: tests/conftest.py
import json
import os

import pytest


# BGM instance
@pytest.fixture(scope='session', autouse=True)
def BGM_env():
  workspace = os.path.dirname(__file__)
  path = os.path.join(workspace, 'data', 'bgm')
  os.environ['VCG_BGM_ROOT'] = path


# input for local workflow testing
@pytest.fixture(scope='function')
def params():
  path = os.path.join(os.path.dirname(__file__), 'data', 'localflow001.json')
  return json.load(open(path))
