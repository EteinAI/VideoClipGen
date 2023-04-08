# Path: tests/test_imageretrieval.py

import pytest
from unittest.mock import patch

import os
from pathlib import Path

from vcg.imageretrieval.retrieval import retrieve
from vcg.imageretrieval.activity import retrieve_image


@pytest.fixture
def summaries():
  return [
    '这145平米的样板间采用10多种色彩, 创造了和谐、高级的空间',
    '客餐厅采用无吊顶设计, 左右清晰分区',
    '墙面、顶面和门框采用黑色金属线条, 营造简约现代感',
    '餐椅和抱枕的脏橘色贯穿客餐厅, 避免了视觉上的割裂感',
    '选择雅琪诺悦动风华系列的窗帘, 营造出温馨的氛围',
    '主卧和次卧都采用了不同的装饰元素, 呈现出不同的风格, 相应地丰富了整个空间'
  ]


@pytest.fixture
def image_files(workspace):
  path = Path(os.path.join(workspace, 'images'))
  return sorted([str(p) for p in path.glob('**/*.jpg')])


def test_retrieve(summaries, image_files):
  selected, _, _ = retrieve(summaries, image_files)
  assert len(selected) == len(summaries)
  for images in selected:
    assert len(images) > 0


@pytest.mark.asyncio
@patch('vcg.imageretrieval.activity.retrieve')
async def test_retrieve_image(mock_retrieve, tmp_path, image_files, params):
  params['cwd'] = tmp_path
  mock_retrieve.return_value = (
    [[i] for i in image_files[:-2]],
    [image_files[-2]],
    [image_files[-1]]
  )

  frames = await retrieve_image(params)

  mock_retrieve.assert_called_once()
  assert len(frames) == len(image_files[:-2])
  assert os.path.exists(os.path.join(tmp_path, 'retrieve', 'selected'))
  assert os.path.exists(os.path.join(tmp_path, 'retrieve', 'kept'))
  assert os.path.exists(os.path.join(tmp_path, 'retrieve', 'dropped'))
