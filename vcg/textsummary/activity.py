import os
import json

from temporalio import activity

from textsummary.summary import proxy_summary


@activity.defn(name='summarize')
async def summarize(params) -> list[str]:
  summaries = proxy_summary('\n'.join(params['sentences']))

  with open(os.path.join(params['cwd'], 'summaries.json'), 'w') as fp:
    json.dump(summaries, fp, ensure_ascii=False, indent=2)
    fp.close()

  return summaries


if __name__ == '__main__':
  from workflow.base import run_activity
  run_activity([summarize], task_queue='text-summary')
