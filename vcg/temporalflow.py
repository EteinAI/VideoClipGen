import os
import asyncio

from datetime import timedelta

from temporalio import activity
from temporalio import workflow
from temporalio import exceptions


@activity.defn(name='prepare')
async def prepare(params) -> str:
  workspace = os.path.join(params['cwd'], params['id'])
  os.makedirs(workspace)
  return workspace


# Import our activity, passing it through the sandbox
with workflow.unsafe.imports_passed_through():
  from urlparser.activity import parse_url
  from textsummary.activity import summarize
  from imageretrieval.activity import retrieve_image
  from speechsynthesis.activity import synthesize_speech
  from videogen.activity import generate_video, concat_video


@workflow.defn
class VideoClipGen:
  @workflow.run
  async def run(self, params):
    print(f'New workflow {workflow.info().run_id}...')
    print(f'Input parameters\n{params}')

    # preprocess workflow parameters
    # TODO Find better algorithm for generating id to make it more readable
    params['id'] = workflow.info().run_id
    params['output'] = params['output'] if 'output' in params else 'output.mp4'
    # TODO More TTS services besides aliyun
    if 'voice_ali' in params:
      params['voice'] = params['voice_ali']

    # prepare workspace for data storage
    cwd = await workflow.execute_activity(
      prepare,
      params,
      task_queue='default',
      schedule_to_close_timeout=timedelta(seconds=30),
    )
    params['cwd'] = cwd

    # url crawler
    params['sentences'], params['images'] = await workflow.execute_activity(
      'parse_url',
      params,
      # task_queue='url-parser',
      schedule_to_close_timeout=timedelta(seconds=30)
    )

    # text summarizer
    params['summaries'] = await workflow.execute_activity(
      'summarize',
      params,
      # task_queue='text-summary',
      schedule_to_close_timeout=timedelta(seconds=60)
    )

    if len(params['images']) < len(params['summaries']):
      raise exceptions.ApplicationError('Too few images compare with summaries')

    frames, audio = await asyncio.gather(
      # retrieve image frames
      workflow.execute_activity(
        'retrieve_image',
        params,
        # task_queue='image-retrieval',
        schedule_to_close_timeout=timedelta(seconds=120)
      ),
      # synthesize speech
      # if `'voice' in params` then use the specified voice
      workflow.execute_activity(
        'synthesize_speech',
        params,
        # task_queue='speech-synthesis',
        schedule_to_close_timeout=timedelta(seconds=120)
      )
    )

    if len(frames) != len(audio):
      raise RuntimeError('Number of frames and audio clips do not match')

    params['assets'] = [{'frames': frames[i], 'audio': audio[i]}
                        for i in range(len(frames))]

    # generate video clips
    params['videos'] = await workflow.execute_activity(
      'generate_video',
      params,
      # task_queue='video-generation',
      schedule_to_close_timeout=timedelta(seconds=60)
    )

    params['output'] = await workflow.execute_activity(
      'concat_video',
      params,
      # task_queue='video-generation',
      schedule_to_close_timeout=timedelta(seconds=60)
    )

    return params


async def main(server: str, task_queue: str):
  from temporalio.client import Client
  from temporalio.worker import Worker

  print('Starting workflow VideoClipGen...')
  print(f'Connecting to server at {server}...')
  print(f'Using task queue {task_queue}...')

  # Create client connected to server at the given address
  client = await Client.connect(server)
  worker = Worker(
    client,
    task_queue=task_queue,
    activities=[prepare, parse_url, summarize, retrieve_image,
                synthesize_speech, generate_video, concat_video],
    workflows=[VideoClipGen]
  )
  await worker.run()


if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument('--server', default='localhost:7233')
  parser.add_argument('--task-queue', default='default')
  args = parser.parse_args()
  server = args.server
  task_queue = args.task_queue

  asyncio.run(main(server, task_queue))
