import asyncio
import logging
import json

from datetime import timedelta

from temporalio import activity
from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError, FailureError


@activity.defn(name='prepare')
async def prepare(params) -> str:
  import os

  # bmg directory
  if os.getenv('VCG_BGM_DIR') is None:
    test_bgm = os.path.abspath(os.path.join(
      os.path.dirname(__file__),
      '../tests/data/bgm',
    ))
    os.environ['VCG_BGM_ROOT'] = os.path.abspath(test_bgm)
  print(f'VCG_BGM_ROOT: {os.getenv("VCG_BGM_ROOT")}')

  # workspace
  cwd = os.getenv('VCG_WORKSPACE', default=os.path.abspath('./data'))
  workspace = os.path.join(cwd, params['id'])
  os.makedirs(workspace)

  return workspace


# Import our activity, passing it through the sandbox
with workflow.unsafe.imports_passed_through():
  from urlparser.activity import parse_url
  from textsummary.activity import summary_and_title
  from speechsynthesis.activity import synthesize_speech
  from videogen.activity import generate_video, concat_video


@workflow.defn
class VideoClipGen:
  def __init__(self):
    self._progress = {
      'runId': '',
      'output': '',
      'prepare': {'status': 'pending', 'startTime': 0},
      'parser': {'status': 'pending', 'startTime': 0},
      'assets': {'status': 'pending', 'startTime': 0},
      'video': {'status': 'pending', 'startTime': 0},
    }

  def _set_progress(self, key: str, status: str, code: str = ''):
    '''
    status: pending, running, success, error, timeout
    code: error code
    '''
    self._progress[key]['status'] = status
    if status == 'running':
      self._progress[key]['startTime'] = round(workflow.time() * 1000)
    else:
      self._progress[key]['endTime'] = round(workflow.time() * 1000)
    if code != '':
      self._progress[key]['code'] = code

  @workflow.query(name='progress')
  def query(self) -> str:
    return json.dumps(self._progress)

  @workflow.run
  async def run(self, params):
    retry_policy = RetryPolicy(
      initial_interval=timedelta(seconds=2),
      maximum_attempts=3,
      non_retryable_error_types=[
        "AttributeError",
        "RuntimeError",
      ],
    )

    print(f'New workflow {workflow.info().run_id}...')
    print(f'Input parameters\n{params}')

    # update workflow status
    self._progress['runId'] = workflow.info().run_id
    self._set_progress('prepare', 'running')

    # preprocess workflow parameters
    # TODO Find better algorithm for generating id to make it more readable
    params['id'] = workflow.info().run_id
    params['output'] = params['output'] if 'output' in params else 'output.mp4'
    # TODO More TTS services besides aliyun
    if 'voice_ali' in params:
      params['voice'] = params['voice_ali']

    # prepare workspace for data storage
    params['cwd'] = await workflow.execute_activity(
      prepare,
      params,
      task_queue='vcg',
      schedule_to_close_timeout=timedelta(seconds=60),
    )

    # update workflow status
    self._set_progress('prepare', 'success')
    self._set_progress('parser', 'running')

    # url crawler
    try:
      params['sentences'], params['images'], params['title'] = (
        await workflow.execute_activity(
          'parse_url',
          params,
          # task_queue='url-parser',
          schedule_to_close_timeout=timedelta(seconds=180),
          retry_policy=retry_policy,
        )
      )
      params['originTitle'] = params['title']
    except FailureError as e:
      # update status
      self._set_progress('parser', 'error', 'UrlParserError')
      logging.exception(e.message)
      raise ApplicationError('Failed to parse URL', e)

    # text summarizer
    try:
      params['summaries'], params['instructions'], params['title'] = \
        await workflow.execute_activity(
          'summary_and_title',
          params,
          # task_queue='text-summary',
          schedule_to_close_timeout=timedelta(seconds=180),
          retry_policy=retry_policy,
        )
    except FailureError as e:
      # update status
      self._set_progress('parser', 'error', 'SummaryError')
      logging.exception(e.message)
      raise ApplicationError('SummaryError', e)

    if len(params['images']) < len(params['summaries']):
      # set status
      self._set_progress('parser', 'error', 'TooFewImages')
      raise ApplicationError('Too few images compare with summaries')
    else:
      self._set_progress('parser', 'success')

    # update workflow status
    self._set_progress('assets', 'running')

    # tts and image retrieval
    try:
      frames, audio = await asyncio.gather(
        # retrieve image frames
        workflow.execute_activity(
          'retrieve_image',
          params,
          task_queue='compute-all',
          schedule_to_close_timeout=timedelta(seconds=300),
          retry_policy=retry_policy,
        ),
        # synthesize speech
        # if `'voice' in params` then use the specified voice
        workflow.execute_activity(
          'synthesize_speech',
          params,
          # task_queue='speech-synthesis',
          schedule_to_close_timeout=timedelta(seconds=300),
          retry_policy=retry_policy,
        )
      )
    except FailureError as e:
      # update status
      self._set_progress('assets', 'error', 'AssetsGenError')
      logging.exception(e.message)
      raise ApplicationError('Failed to generate image/wav.', e)

    if len(frames) != len(audio):
      self._set_progress('assets', 'error', 'AssetsMismatch')
      raise ApplicationError('Number of frames and audio clips do not match')
    else:
      self._set_progress('assets', 'success')

    params['assets'] = [{'frames': frames[i], 'audio': audio[i]}
                        for i in range(len(frames))]

    # update workflow status
    self._set_progress('video', 'running')

    try:
      # generate video clips
      params['videos'] = await workflow.execute_activity(
        'generate_video',
        params,
        # task_queue='video-generation',
        schedule_to_close_timeout=timedelta(seconds=180),
        retry_policy=retry_policy,
      )
    except FailureError as e:
      # update status
      self._set_progress('video', 'error', 'VideoGenError')
      logging.exception(e.message)
      raise ApplicationError('Failed to generate videos.', e)

    if len(params['videos']) != len(audio):
      self._set_progress('video', 'error', 'VideoGenError')
      raise ApplicationError('Number of video and audio clips do not match')

    # concat video clips
    try:
      params['video'], params['bgm'], params['kfa'] = (
        await workflow.execute_activity(
          'concat_video',
          params,
          # task_queue='video-generation',
          schedule_to_close_timeout=timedelta(seconds=180),
          retry_policy=retry_policy,
        )
      )
    except FailureError as e:
      # update status
      self._set_progress('video', 'error', 'VideoConcatError')
      logging.exception(e.message)
      raise ApplicationError('Failed to concat videos.', e)

    # update workflow status
    self._set_progress('video', 'success')
    self._progress['title'] = params['title']
    self._progress['output'] = '/'.join([params['id'], params['output']])

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
    activities=[prepare, parse_url, summary_and_title,
                synthesize_speech, generate_video, concat_video],
    workflows=[VideoClipGen]
  )
  await worker.run()


if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument('--server', default='localhost:7233')
  parser.add_argument('--task-queue', default='vcg')
  args = parser.parse_args()
  server = args.server
  task_queue = args.task_queue

  asyncio.run(main(server, task_queue))
