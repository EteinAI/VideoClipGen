import os
import shutil

from temporalio import activity

from videogen.bgm import BGM
from videogen.ffmpegcli import generate, keyframe, concat, audio_mix


@activity.defn(name='generate_video')
async def generate_video(params) -> list[str]:
  print('Generating video...')

  workspace = os.path.join(params['cwd'], 'video')
  if not os.path.exists(workspace):
    os.makedirs(workspace)

  return generate(assets=params['assets'], cwd=workspace)


@activity.defn(name='concat_video')
async def concat_video(params) -> tuple[str, str, list[str]]:
  print('Concatenating video...')

  workspace = os.path.join(params['cwd'], 'video')
  if not os.path.exists(workspace):
    os.makedirs(workspace)

  # HACK hardcoded keyframe animations
  videos, kfa = keyframe(videos=params['videos'], cwd=workspace)

  # TODO dont generate temp file, use ffmpeg pipe instead
  temp = concat(
    videos=videos,
    subtitles=params['subtitles'] if 'subtitles' in params else None,
    size=params['size'] if 'size' in params else None,
    output=os.path.join(params['cwd'], 'temp.mp4'),
  )

  # add background music
  output = os.path.join(params['cwd'], params['output'])
  _, bgm_file = BGM.instance().random()
  if bgm_file == '':
    shutil.copyfile(temp, output)
    return output, '', kfa
  else:
    return audio_mix(temp, bgm_file, output=output), bgm_file, kfa


if __name__ == '__main__':
  from utils.workflow import run_activity
  run_activity([generate_video, concat_video], task_queue='video-generation')
