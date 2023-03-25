# Path: tests/test_imageretrieval.py

import pytest

import os
from pathlib import Path

from vcg.imageretrieval.retrieval import retrieve


@pytest.fixture
def summaries():
  return [
    '这145平米的样板间采用10多种色彩，创造了和谐、高级的空间',
    '客餐厅采用无吊顶设计，左右清晰分区',
    '墙面、顶面和门框采用黑色金属线条，营造简约现代感',
    '餐椅和抱枕的脏橘色贯穿客餐厅，避免了视觉上的割裂感',
    '选择雅琪诺悦动风华系列的窗帘，营造出温馨的氛围',
    '主卧和次卧都采用了不同的装饰元素，呈现出不同的风格，相应地丰富了整个空间'
  ]


@pytest.fixture
def image_files():
  path = Path(os.path.join(os.path.dirname(__file__), 'data', 'images'))
  return sorted([*path.glob('**/*.jpg')])


def test_retrieve(summaries, image_files):
  selected, _, _ = retrieve(summaries, image_files)
  assert len(selected) == len(summaries)
  for images in selected:
    assert len(images) > 0
