import os

from temporalio import activity

from videogen.ffmpegcli import generate, concat


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
  output = os.path.join(params['cwd'], params['output'])
  return concat(videos=params['videos'], output=output)


if __name__ == '__main__':
  from workflow.base import run_activity
  run_activity([generate_video, concat_video], task_queue='video-generation')
