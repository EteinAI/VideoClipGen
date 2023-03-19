# Path: test/test_urlparser.py

import os

from vcg.urlparser.parser import parse


def test_parse(tmp_path):
  parse(
    url='https://mp.weixin.qq.com/s/f3NSyxcbadh5l99ARBnN3w',
    path=tmp_path
  )
  assert os.path.exists(os.path.join(tmp_path, 'images'))
  assert os.path.exists(os.path.join(tmp_path, 'metadata.json'))
  assert os.path.exists(os.path.join(tmp_path, 'sentences.json'))
