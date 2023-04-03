import os

from temporalio import activity

from videogen.bgm import BGM
from videogen.ffmpegcli import generate, concat, audio_mix


@activity.defn(name='generate_video')
async def generate_video(params) -> list[str]:
  print('Generating video...')

  workspace = os.path.join(params['cwd'], 'video')
  if not os.path.exists(workspace):
    os.makedirs(workspace)

  return generate(assets=params['assets'], cwd=workspace)


@activity.defn(name='concat_video')
async def concat_video(params) -> str:
  print('Concatenating video...')

  # TODO dont generate temp file, use ffmpeg pipe instead
  temp = concat(videos=params['videos'],
                output=os.path.join(params['cwd'], 'temp.mp4'))
  output = os.path.join(params['cwd'], params['output'])

  _, bgm_file = BGM.instance().random()
  params['bgm'] = bgm_file

  return audio_mix(temp, bgm_file, output=output)


if __name__ == '__main__':
  from workflow.base import run_activity
  run_activity([generate_video, concat_video], task_queue='video-generation')
