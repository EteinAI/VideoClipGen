# Path: tests/test_tts.py

import pytest

from vcg.speechsynthesis.alitts import create_token, tts


# token
token, expire_time = create_token()
print(f'Token: {token}')
print(f'Expire time: {expire_time}')


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


@pytest.mark.parametrize('voice', [
  'kenny',
  'zhiyan_emo',
])
def test_tts(summaries, tmp_path, voice):
  wav_files = tts(summaries, tmp_path, voice)
  assert len(wav_files) == len(summaries)
