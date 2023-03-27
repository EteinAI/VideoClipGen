import os
import json
import importlib

from temporalio import activity

from textsummary.summary import proxy_summary
from textsummary.prompts import SimplePrompter


def create_prompter(classname):
  module = importlib.import_module('textsummary.prompts')
  class_ = getattr(module, classname)
  return class_() if class_ else SimplePrompter()


@activity.defn(name='summarize')
async def summarize(params) -> tuple[list[str], list[str]]:
  prompter = create_prompter(
    classname=params['prompter']
  ) if 'prompter' in params else SimplePrompter()

  summaries, instructions = proxy_summary(
    text='\n'.join(params['sentences']),
    prompter=prompter
  )

  with open(os.path.join(params['cwd'], 'summaries.json'), 'w') as fp:
    json.dump(summaries, fp, ensure_ascii=False, indent=2)
    fp.close()
  with open(os.path.join(params['cwd'], 'instructions.json'), 'w') as fp:
    json.dump(instructions, fp, ensure_ascii=False, indent=2)
    fp.close()

  return summaries, instructions


if __name__ == '__main__':
  from workflow.base import run_activity
  run_activity([summarize], task_queue='text-summary')
