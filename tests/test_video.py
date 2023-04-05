# Path test/test_video.py

import pytest

import ffmpeg
import os
from pathlib import Path

from vcg.videogen.ffmpegcli import generate, keyframe, concat, audio_mix


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
def assets():
  # summaries of this video
  # summaries = [
  #   '这145平米的样板间采用10多种色彩，创造了和谐、高级的空间',
  #   '客餐厅采用无吊顶设计，左右清晰分区',
  #   '墙面、顶面和门框采用黑色金属线条，营造简约现代感',
  #   '餐椅和抱枕的脏橘色贯穿客餐厅，避免了视觉上的割裂感',
  #   '选择雅琪诺悦动风华系列的窗帘，营造出温馨的氛围',
  #   '主卧和次卧都采用了不同的装饰元素，呈现出不同的风格，相应地丰富了整个空间'
  # ]

  # workspace
  workspace = os.path.dirname(__file__)
  # images
  frame_path = Path(os.path.join(workspace, 'data', 'images'))
  frames = [[f] for f in sorted([*frame_path.glob('**/*.jpg')])]
  # audio
  audio_path = Path(os.path.join(workspace, 'data', 'audio'))
  audio = sorted([*audio_path.glob('**/*.wav')])
  # assets
  return [{'frames': frames[i], 'audio': audio[i]} for i in range(len(audio))]


def test_generate(assets, tmp_path):
  videos = generate(assets=assets, cwd=tmp_path, verbose=True)
  assert len(videos) == len(assets)
  for video in videos:
    assert os.path.exists(video)
    valid, _ = validation(video)
    assert valid


def test_keyframe(assets, tmp_path):
  videos = generate(assets=assets, cwd=tmp_path, verbose=True)
  outputs, names = keyframe(videos=videos, cwd=tmp_path)
  assert len(outputs) == len(videos)
  assert len(names) == len(videos)
  for output in outputs:
    assert os.path.exists(output)
    valid, _ = validation(output)
    assert valid


def test_concat(assets, tmp_path):
  videos = generate(assets=assets, cwd=tmp_path, verbose=True)
  outputs, _ = keyframe(videos=videos, cwd=tmp_path)
  # videos = [os.path.join(tmp_path, f'{i}.mp4')
  #           for i in range(len(assets))]
  output = concat(videos=outputs, output=os.path.join(tmp_path, 'output.mp4'))
  assert os.path.exists(output)
  valid, _ = validation(output)
  assert valid


@pytest.fixture
def bgms():
  workspace = os.path.dirname(__file__)
  bgm_path = Path(os.path.join(workspace, 'data', 'bgm'))
  return sorted([*bgm_path.glob('**/*.m4a')])


# @pytest.mark.parametrize('bgmusic', *pytest.lazy_fixture('bgms'))
def test_audio_mix(assets, tmp_path, BGM_instance):
  videos = generate(assets=assets, cwd=tmp_path, verbose=True)
  outputs, _ = keyframe(videos=videos, cwd=tmp_path)
  output = concat(videos=outputs, output=os.path.join(tmp_path, 'output.mp4'))

  all = BGM_instance.all()
  for i, key in enumerate(all):
    mixed = os.path.join(tmp_path, f'output{i}.mp4')
    mixed = audio_mix(output, BGM_instance[key], mixed)
    valid, _ = validation(mixed)
    assert valid
