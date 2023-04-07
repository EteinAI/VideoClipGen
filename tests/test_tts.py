# Path: tests/test_tts.py

import pytest
from unittest.mock import patch

import os

from vcg.speechsynthesis.alitts import create_token, tts
from vcg.speechsynthesis.activity import synthesize_speech

# token
token, expire_time = create_token()
print(f'Token: {token}')
print(f'Expire time: {expire_time}')


@pytest.fixture
def summaries():
  return [
    '这145平米的样板间采用10多种色彩, 创造了和谐、高级的空间',
    '主卧和次卧都采用了不同的装饰元素, 呈现出不同的风格, 相应地丰富了整个空间'
  ]


@pytest.mark.parametrize('voice', [
  'kenny',
  'zhiyan_emo',
])
def test_tts(summaries, tmp_path, voice):
  wav_files = tts(summaries, tmp_path, voice)
  assert len(wav_files) == len(summaries)


@pytest.mark.asyncio
@patch('vcg.speechsynthesis.activity.tts')
async def test_synthesize_speech(mock_tts, tmp_path, params):
  params['cwd'] = tmp_path
  mock_tts.return_value = params['audio']

  wav_files = await synthesize_speech(params)

  mock_tts.assert_called_once()
  assert wav_files == params['audio']
  assert os.path.exists(os.path.join(params['cwd'], 'wav'))

  mock_tts.return_value = []
  with pytest.raises(RuntimeError) as e:
    wav_files = await synthesize_speech(params)
    assert 'Only 0 wav generated' in str(e.value)
