
import argparse
import asyncio
import json
import os
import time
from pathlib import Path

from speechsynthesis.activity import synthesize_speech
from videogen.activity import generate_video, concat_video


# use bgm testing dat if VCG_BGM_ROOT is not set
test_bgm = os.path.abspath(os.path.join(
  os.path.dirname(__file__),
  '../tests/data/bgm',
))
os.environ['VCG_BGM_ROOT'] = os.path.abspath(test_bgm)
print(f'VCG_BGM_ROOT: {os.getenv("VCG_BGM_ROOT")}')


async def main(params):
  print(f'Inputs: {params}')

  cwd = params['cwd'] if 'cwd' in params else os.path.abspath('./data')
  params['id'] = time.strftime('%Y%m%d-%H%M%S', time.localtime())
  params['voice'] = params['voice_ali'] if 'voice_ali' in params else 'kenny'

  # prepare workspace
  workspace = os.path.abspath(os.path.join(cwd, params['id']))
  os.makedirs(workspace)
  params['cwd'] = workspace
  print(f'Workspace: {workspace}')

  # image retrieval and speech synthesis
  path = Path(params['imagePath'])
  frames = []
  for img in params['images']:
    frames.append([*path.glob(str(img) + '.png'),
                  *path.glob(str(img) + '.jpg'),
                  *path.glob(str(img) + '.jpeg')])
  # frames = sorted([str(f)] for f in [
  #   *path.glob('**/*.png'),
  #   *path.glob('**/*.jpg'),
  #   *path.glob('**/*.jpeg'),
  # ])
  print('images:', frames)
  audio, params['subtitles'] = await synthesize_speech(params)

  if len(frames) != len(audio):
    print('Number of frames and audio clips do not match')

  params['assets'] = [{'frames': frames[i], 'audio': audio[i]}
                      for i in range(len(audio))]

  # generate video clips
  params['videos'] = await generate_video(params)
  if len(params['videos']) != len(audio):
    raise RuntimeError('Number of video and audio clips do not match')

  # concat video clips
  title = params['title'] if 'title' in params else 'Untitled'
  params['size'] = (1280, 720)
  params['output'] = f'{title}.mp4'
  output, bgm, kfa = await concat_video(params)

  print(f'BGM: {bgm}')
  print(f'Keyframe animations: {kfa}')
  print(f'Final output: {output}')

  return output


def parse_args():
  parser = argparse.ArgumentParser()
  parser.add_argument('--params', required=True, type=str)
  parser.add_argument('--cwd', type=str)
  parser.add_argument('--image-path', type=str)
  parser.add_argument('--voice-ali', type=str)
  parser.add_argument('--summaries', type=str)

  args = parser.parse_args()
  print(f'params: {args.params}')
  param_file = os.path.abspath(args.params)
  if not os.path.exists(param_file):
    raise RuntimeError(f'Params file {param_file} does not exist')

  with open(args.params, 'rb') as fp:
    params = json.load(fp)
    if args.cwd:
      params['cwd'] = args.cwd
    if args.image_path:
      params['imagePath'] = args.image_path
    if args.voice_ali:
      params['voice_ali'] = args.voice_ali
    if args.summaries:
      params['summaries'] = args.summaries

    return params


if __name__ == '__main__':
  asyncio.run(main(parse_args()))
