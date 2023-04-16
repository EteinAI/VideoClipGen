# Path test/test_video.py

import pytest
from unittest.mock import patch

import ffmpeg
import os
from pathlib import Path

from vcg.videogen.ffmpegcli import generate, keyframe, concat, audio_mix
from vcg.videogen.activity import generate_video, concat_video
from vcg.videogen.bgm import BGM


def validation(filename):
  output_arguments = {
    'hide_banner': None,
    'err_detect': 'compliant',
    'loglevel': 'error'
  }
  _, stderr = ffmpeg.input(
    filename,
    **output_arguments
  ).output(
    'pipe:',
    format='null'
  ).run(
    capture_stdout=True,
    capture_stderr=True,
    overwrite_output=True
  )
  if 'error' in str(stderr).lower():
    return False, stderr.decode('utf-8')
  else:
    return True, 'valid video'


@pytest.fixture
def assets(workspace):
  # summaries of this video
  # summaries = [
  #   '这145平米的样板间采用10多种色彩，创造了和谐、高级的空间',
  #   '客餐厅采用无吊顶设计，左右清晰分区',
  #   '墙面、顶面和门框采用黑色金属线条，营造简约现代感',
  #   '餐椅和抱枕的脏橘色贯穿客餐厅，避免了视觉上的割裂感',
  #   '选择雅琪诺悦动风华系列的窗帘，营造出温馨的氛围',
  #   '主卧和次卧都采用了不同的装饰元素，呈现出不同的风格，相应地丰富了整个空间'
  # ]

  # images
  frame_path = Path(os.path.join(workspace, 'images'))
  frames = [[f] for f in sorted([*frame_path.glob('**/*.jpg')])]
  # audio
  audio_path = Path(os.path.join(workspace, 'audio'))
  audio = sorted([*audio_path.glob('**/*.wav')])
  # assets
  return [{'frames': frames[i], 'audio': audio[i]} for i in range(len(audio))]


@pytest.fixture
def subtitles(workspace):
  path = Path(os.path.join(workspace, 'audio'))
  return sorted([*path.glob('**/*.ssa')])


def test_generate(assets, tmp_path):
  videos = generate(assets=assets, cwd=tmp_path, verbose=True)
  assert len(videos) == len(assets)
  for video in videos:
    assert os.path.exists(video)
    valid, _ = validation(video)
    assert valid


def test_keyframe(assets, tmp_path):
  videos = generate(assets=assets, cwd=tmp_path, verbose=True)
  outputs, names = keyframe(videos=videos, cwd=tmp_path, verbose=True)
  assert len(outputs) == len(videos)
  assert len(names) == len(videos)
  for output in outputs:
    assert os.path.exists(output)
    valid, _ = validation(output)
    assert valid


def test_concat(assets, subtitles, tmp_path):
  videos = generate(assets=assets, cwd=tmp_path, verbose=True)
  # videos = [os.path.join(tmp_path, f'{i}.mp4')
  #           for i in range(len(assets))]

  with pytest.raises(RuntimeError) as e:
    concat(
      videos=videos,
      size=(100, -100),
      output=os.path.join(tmp_path, 'concat.mp4'),
      verbose=True,
    )
  assert 'Failed to concatenate videos' in str(e)

  with pytest.raises(RuntimeError) as e:
    concat(videos=[], output=os.path.join(tmp_path, 'concat.mp4'))
  assert 'Failed to assemble stream' in str(e)

  with pytest.raises(ValueError) as e:
    concat(videos=videos, subtitles=['random'],
           output=os.path.join(tmp_path, 'concat.mp4'))
  assert 'must be the same' in str(e)

  output = concat(
    videos=videos,
    subtitles=subtitles,
    output=os.path.join(tmp_path, 'output.mp4'),
    verbose=True,
  )
  assert os.path.exists(output)
  valid, _ = validation(output)
  assert valid


def bgms(workspace):
  bgm_path = Path(os.path.join(workspace, 'bgm'))
  return sorted([*bgm_path.glob('**/*.m4a')])


# TODO reuse concat test result
# @pytest.mark.parametrize('bgm', bgms())
def test_audio_mix(assets, tmp_path):
  videos = generate(assets=assets, cwd=tmp_path, verbose=True)
  output = concat(videos=videos, output=os.path.join(tmp_path, 'output.mp4'))

  with pytest.raises(RuntimeError) as e:
    audio_mix(output, 'not_exist.mp3', 'mixed.mp4')
  assert 'Failed to add background music' in str(e)

  mixed = os.path.join(tmp_path, 'with_bgm.mp4')
  mixed = audio_mix(output, BGM.instance().random()[1], mixed)
  valid, _ = validation(mixed)
  assert valid


@pytest.mark.asyncio
@patch('vcg.videogen.activity.generate')
async def test_generate_video(mock_generate, tmp_path, params):
  params['cwd'] = tmp_path
  mock_generate.return_value = params['videos']

  videos = await generate_video(params)

  mock_generate.assert_called_once()
  assert videos == params['videos']
  assert os.path.exists(os.path.join(params['cwd'], 'video'))


@pytest.mark.asyncio
@patch('vcg.videogen.activity.keyframe')
@patch('vcg.videogen.activity.audio_mix')
@patch('vcg.videogen.activity.concat')
async def test_concat_video(
  mock_concat,
  mock_audio_mix,
  mock_keyframe,
  tmp_path, params
):
  params['cwd'] = tmp_path

  mock_concat.return_value = 'concat.mp4'
  mock_audio_mix.return_value = 'output.mp4'
  mock_keyframe.return_value = (
    params['videos'],
    params['kfa'],
  )

  final_output, bgm, kfa = await concat_video(params)

  assert kfa == params['kfa']
  assert mock_keyframe.call_count == 1
  assert mock_keyframe.call_args.kwargs == {
    'videos': params['videos'],
    'cwd': os.path.join(params['cwd'], 'video'),
  }

  assert os.path.exists(os.path.join(params['cwd'], 'video'))
  assert mock_concat.call_count == 1

  assert os.path.exists(bgm)
  assert final_output == 'output.mp4'
  assert mock_audio_mix.call_count == 1
  assert mock_audio_mix.call_args.args == ('concat.mp4', bgm)
