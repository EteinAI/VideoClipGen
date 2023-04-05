# Path: tests/test_bgm.py

import pytest

import os

from vcg.videogen.bgm import BGM


def test_BGM_empty():
  bgm = BGM(path=os.path.join(os.path.dirname(__file__), 'data', 'images'))
  assert len(bgm) == 0
  assert bgm.all() == []
  assert bgm.random() == ('', '')


def test_BGM_root():
  with pytest.raises(RuntimeError) as e:
    _ = BGM(path='/path/not/exists')
    assert 'not exists' in str(e.value)
  with pytest.raises(RuntimeError) as e:
    tmp = os.getenv('VCG_BGM_ROOT')
    if tmp is not None:
      del os.environ['VCG_BGM_ROOT']
    _ = BGM()
    assert 'not specified' in str(e.value)
    if tmp is not None:
      os.environ['VCG_BGM_ROOT'] = tmp


def test_BGM_singleton():
  with pytest.raises(RuntimeError) as e:
    tmp = os.getenv('VCG_BGM_ROOT')
    if tmp is not None:
      del os.environ['VCG_BGM_ROOT']
    _ = BGM.instance()
    assert 'not specified' in str(e.value)
    if tmp is not None:
      os.environ['VCG_BGM_ROOT'] = tmp

  tmp = os.getenv('VCG_BGM_ROOT')
  root = os.path.join(os.path.dirname(__file__), 'data', 'bgm')
  os.environ['VCG_BGM_ROOT'] = root
  bgm = BGM.instance()
  if tmp is not None:
    os.environ['VCG_BGM_ROOT'] = tmp
  else:
    del os.environ['VCG_BGM_ROOT']

  assert bgm is not None
  assert root == str(bgm._root)
  assert bgm == BGM.instance()
