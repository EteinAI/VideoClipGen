# Path: tests/test_tts.py

import pytest
from unittest.mock import patch

import os
import json
from datetime import datetime, timedelta
from pysubs2 import SSAFile

from vcg.speechsynthesis.activity import synthesize_speech
from vcg.speechsynthesis.alitts import (
  check_env,
  create_token,
  tts,
  tts_with_subtitle,
)
from vcg.speechsynthesis.subtitle import (
  tokenize,
  wording,
  subtitle,
)


def test_create_token():
  token, expire = create_token()
  assert token != ''
  assert datetime.fromtimestamp(expire) - datetime.now() > timedelta(days=1)

  with patch.dict('os.environ', {'ALI_ACCESSKEY_ID': 'bad-id'}):
    assert create_token() == ('', 0)

  with patch.dict('os.environ', {'ALI_ACCESSKEY_SECRET': 'bad-secret'}):
    assert create_token() == ('', 0)


def test_check_env():
  with patch.dict('os.environ'):
    del os.environ['ALI_ACCESSKEY_ID']

    with pytest.raises(RuntimeError) as e:
      @check_env('ALI_ACCESSKEY_ID')
      def dummy():
        pass
    assert 'ALI_ACCESSKEY_ID not found in env or in .env file' in str(e.value)


@pytest.fixture
def summaries():
  return [
    '这145平米的样板间采用10多种色彩, 创造了和谐、高级的空间',
    '客餐厅采用无吊顶设计，左右清晰分区',
    '墙面、顶面和门框采用黑色金属线条，营造简约现代感',
    '餐椅和抱枕的脏橘色贯穿客餐厅，避免了视觉上的割裂感',
    '选择雅琪诺悦动风华系列的窗帘，营造出温馨的氛围',
    '主卧和次卧都采用了不同的装饰元素, 呈现出不同的风格, 相应地丰富了整个空间',
  ]


@pytest.mark.parametrize('voice', [
  'kenny',
  'zhiyan_emo',
])
def test_tts(summaries, tmp_path, voice):
  wav_files = tts(summaries, tmp_path, voice)
  assert len(wav_files) == len(summaries)


@pytest.mark.parametrize('voice', [
  'kenny',
])
def test_tts_with_subtitle(summaries, tmp_path, voice):
  wav_files, ssa_files = tts_with_subtitle(summaries, tmp_path, voice)
  assert len(wav_files) == len(summaries)
  for f in wav_files:
    assert os.path.exists(f)
  assert len(ssa_files) == len(summaries)
  for f in ssa_files:
    assert os.path.exists(f)


@patch('vcg.speechsynthesis.alitts.create_token')
def test_tts_with_subtitle_mock(mock_token, summaries, tmp_path):
  mock_token.return_value = ('bad-token', 0)
  with pytest.raises(RuntimeError) as e:
    _, _ = tts_with_subtitle(summaries, tmp_path, 'kenny')
  assert 'No metadata received' in str(e.value)
  assert mock_token.call_count == 1

  mock_token.return_value = ('', 0)
  with pytest.raises(ValueError) as e:
    _, _ = tts_with_subtitle(summaries, tmp_path, 'kenny')
  assert 'Token is required for websocket tts' in str(e.value)
  assert mock_token.call_count == 2


@pytest.mark.asyncio
@patch('vcg.speechsynthesis.activity.tts_with_subtitle')
async def test_synthesize_speech(mock_tts, tmp_path, params):
  params['cwd'] = tmp_path
  mock_tts.return_value = (params['audio'], params['subtitles'])

  wav_files, ssa_files = await synthesize_speech(params)

  mock_tts.assert_called_once()
  assert wav_files == params['audio']
  assert ssa_files == params['subtitles']
  assert os.path.exists(os.path.join(params['cwd'], 'wav'))

  mock_tts.return_value = ([], [])
  with pytest.raises(RuntimeError) as e:
    wav_files, ssa_files = await synthesize_speech(params)
  assert 'Only 0 wav generated while expecting' in str(e.value)

  mock_tts.return_value = (params['audio'], [])
  with pytest.raises(RuntimeError) as e:
    wav_files, ssa_files = await synthesize_speech(params)
  assert 'Wave files and subtitles do not match' in str(e.value)


@pytest.fixture
def ts_data(request, workspace):
  idx = request.param
  path = os.path.join(workspace, 'ssa')
  sent_file = os.path.join(path, 'sentences.json')
  ts_file = os.path.join(path, f'{idx}.json')
  ssa_file = os.path.join(path, f'{idx}.ssa')

  sentence = json.load(open(sent_file, 'r'))[idx]
  ts = json.load(open(ts_file, 'r'))['payload']['subtitles']
  events = SSAFile.load(ssa_file).events

  return sentence, ts, events


@pytest.mark.parametrize(
  'ts_data',
  range(17),
  indirect=True,
)
def test_subtitle(ts_data):
  sentence, ts, events = ts_data

  tokens = tokenize(ts, sentence)
  lines = wording(tokens)
  ssa = subtitle(lines, (720, 1280))
  for e1, e2 in zip(ssa.events, events):
    assert round(e1.start / 10) == round(e2.start / 10)
    assert round(e1.end / 10) == round(e2.end / 10)
    assert e1.text == e2.text
