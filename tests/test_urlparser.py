# Path: test/test_urlparser.py

import pytest
from unittest.mock import patch

import os

from vcg.urlparser.parser import parse
from vcg.urlparser.activity import parse_url


def test_parse(tmp_path):
  parse(
    url='https://mp.weixin.qq.com/s/f3NSyxcbadh5l99ARBnN3w',
    path=tmp_path
  )
  assert os.path.exists(os.path.join(tmp_path, 'images'))
  assert os.path.exists(os.path.join(tmp_path, 'metadata.json'))
  assert os.path.exists(os.path.join(tmp_path, 'sentences.json'))


@pytest.mark.asyncio
@patch('vcg.urlparser.activity.parse')
async def test_parse_url(mock_parse, params):
  mock_parse.return_value = (
    params['sentences'],
    params['images'],
    {'title': params['title']},
  )

  texts, images, title = await parse_url(params)

  assert texts == params['sentences']
  assert images == params['images']
  assert title == params['title']

  mock_parse.assert_called_once()
  assert mock_parse.call_args.args == (params['url'], params['cwd'])
