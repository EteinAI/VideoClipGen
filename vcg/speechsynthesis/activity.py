import os

from temporalio import activity

from speechsynthesis.alitts import tts


@activity.defn(name='synthesize_speech')
async def synthesize_speech(params) -> list[str]:
  workspace = os.path.join(params['cwd'], 'wav')
  if not os.path.exists(workspace):
    os.makedirs(workspace)

  wav_files = tts(
    texts=params['summaries'],
    cwd=workspace,
    voice=params['voice'] if 'voice' in params else None
  )

  num_wav = len(wav_files)
  num_summary = len(params['summaries'])
  if not num_wav == num_summary:
    raise RuntimeError(
      f'Only {num_wav} wav generated while expecting {num_summary}')

  return wav_files


if __name__ == '__main__':
  from workflow.base import run_activity
  run_activity([synthesize_speech], task_queue='speech-synthesis')
