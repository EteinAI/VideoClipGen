
import argparse
import asyncio
import json
import os
import time

from urlparser.activity import parse_url
from textsummary.activity import summary_and_title
from imageretrieval.activity import retrieve_image
from speechsynthesis.activity import synthesize_speech
from videogen.activity import generate_video, concat_video


async def main(params):
  print(f'Inputs: {params}')

  params['id'] = time.strftime('%Y%m%d-%H%M%S', time.localtime())
  if 'voice_ali' in params:
    params['voice'] = params['voice_ali']

  # prepare workspace
  workspace = os.path.abspath(os.path.join(params['cwd'], params['id']))
  os.makedirs(workspace)
  params['cwd'] = workspace
  print(f'Workspace: {workspace}')

  # parse url
  params['sentences'], params['images'] = await parse_url(params)

  # text summarizer
  params['summaries'], params['instructions'], title = await summary_and_title(params)
  print(f'Title: {title}')

  # image retrieval and speech synthesis
  frames = await retrieve_image(params)
  audio = await synthesize_speech(params)

  if len(frames) != len(audio):
    raise RuntimeError('Number of frames and audio clips do not match')

  params['assets'] = [{'frames': frames[i], 'audio': audio[i]}
                      for i in range(len(frames))]

  # generate video clips
  params['videos'] = await generate_video(params)
  if len(params['videos']) != len(audio):
    raise RuntimeError('Number of video and audio clips do not match')

  # concat video clips
  params['output'] = f'{title}.mp4'
  output = await concat_video(params)
  print(f'Final output: {output}')

  return output


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--params', required=True, type=str)
  parser.add_argument('--cwd', type=str)
  parser.add_argument('--url', type=str)
  parser.add_argument('--voice-ali', type=str)
  parser.add_argument('--prompter', type=str)

  args = parser.parse_args()
  with open(args.params, 'rb') as fp:
    params = json.load(fp)
    if args.cwd:
      params['cwd'] = args.cwd
    if args.url:
      params['url'] = args.url
    if args.voice_ali:
      params['voice_ali'] = args.voice_ali
    if args.prompter:
      params['prompter'] = args.prompter
    asyncio.run(main(params))
