# Path: tests/test_bgm.py

import pytest
from unittest.mock import patch

import os

from vcg.videogen.bgm import BGM


def test_BGM_instance():
  bgm = BGM()
  assert len(bgm) != 0
  assert bgm.all() != []
  assert bgm.random() != ('', '')


def test_BGM_empty(workspace):
  bgm = BGM(path=os.path.join(workspace, 'images'))
  assert len(bgm) == 0
  assert bgm.all() == []
  assert bgm.random() == ('', '')


def test_BGM_root():
  with pytest.raises(RuntimeError) as e:
    _ = BGM(path='/path/not/exists')
  assert 'not exists' in str(e.value)

  with patch.dict('os.environ', {'VCG_BGM_ROOT': '/path/not/exists'}):
    with pytest.raises(RuntimeError) as e:
      _ = BGM()
    assert 'not exists' in str(e.value)

  with patch.dict('os.environ'):
    del os.environ['VCG_BGM_ROOT']
    with pytest.raises(RuntimeError) as e:
      _ = BGM()
    assert 'not specified' in str(e.value)


def test_BGM_singleton(workspace):
  with patch.dict('os.environ'):
    del os.environ['VCG_BGM_ROOT']
    with pytest.raises(RuntimeError) as e:
      _ = BGM.instance()
    assert 'not specified' in str(e.value)

  with patch.dict('os.environ'):
    root = os.path.join(workspace, 'bgm')
    os.environ['VCG_BGM_ROOT'] = root
    bgm = BGM.instance()
    assert bgm is not None
    assert root == str(bgm._root)
    assert bgm == BGM.instance()
