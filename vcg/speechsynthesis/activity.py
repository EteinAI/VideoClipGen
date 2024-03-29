import os

from temporalio import activity

from .alitts import tts_with_subtitle


@activity.defn(name='synthesize_speech')
async def synthesize_speech(params):
  workspace = os.path.join(params['cwd'], 'wav')
  if not os.path.exists(workspace):
    os.makedirs(workspace)

  wav_files, ssa_files = tts_with_subtitle(
    texts=params['summaries'],
    cwd=workspace,
    voice=params['voice'] if 'voice' in params else None,
  )

  num_wav = len(wav_files)
  num_subtitle = len(ssa_files)
  num_summary = len(params['summaries'])
  if num_wav != num_summary:
    raise RuntimeError(
      f'Only {num_wav} wav generated while expecting {num_summary}')
  if num_wav != num_subtitle:
    raise RuntimeError(
      f'Wave files and subtitles do not match: {num_wav} vs {num_subtitle}')

  return wav_files, ssa_files


if __name__ == '__main__':
  from workflow.base import run_activity
  run_activity([synthesize_speech], task_queue='speech-synthesis')
