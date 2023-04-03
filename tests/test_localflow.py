# path: tests/test_localflow.py

import os
import pytest

from unittest.mock import mock_open, patch, MagicMock

from vcg.localflow import main, parse_args


# How to mock open()
# @patch('builtins.open', MockOpen().open)
# class MockOpen:
#   builtin_open = open
#
#   def open(self, *args, **kwargs):
#     if args[0] == 'dummy.json':
#       return mock_open(read_data="bar")(*args, **kwargs)
#     return self.builtin_open(*args, **kwargs)


@pytest.mark.asyncio
async def test_main(tmp_path):
  # Set up the mock arguments with a dummy file path
  params = {
    'cwd': tmp_path,
    'url': 'https://mp.weixin.qq.com/s/WRCfatBGqWzAxaV-kWEJ4Q',
    'voice_ali': 'kenny',
    'prompter': 'ScenePrompter',
  }

  # set VCG_BGM_ROOT
  workspace = os.path.dirname(__file__)
  os.environ['VCG_BGM_ROOT'] = os.path.join(workspace, 'data', 'bgm')

  output = await main(params)
  assert os.path.exists(output)


@patch('argparse.ArgumentParser.parse_args')
def test_parse_args(
  mock_args,
):
  args = MagicMock()
  args.params = 'dummy.json'
  mock_args.return_value = args
  with pytest.raises(RuntimeError) as e:
    parse_args()
    assert 'does not exist' in str(e.value)


# @patch('argparse.ArgumentParser.parse_args')
# @patch('json.load')
# def test_parse_args2(
#   mock_load,
#   mock_args,
# ):
#   args = MagicMock()
#   args.params = 'dummy.json'
#   mock_args.return_value = args
#   mock_load.return_value = {}
#   with patch('os.path.exists', return_value=True):
#     with patch('builtins.open', mock_open(read_data='')):
#       # with pytest.raises(RuntimeError) as e:
#       parse_args()
#       # assert 'URL is not set' in str(e.value)
