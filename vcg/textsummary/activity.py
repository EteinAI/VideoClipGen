import os
import json
import importlib

from temporalio import activity

from textsummary.summary import proxy_summary, proxy_summary_title
from textsummary.prompts import SimplePrompter, TitleSimplePrompter


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


@activity.defn(name='summary_and_title')
async def summary_and_title(params) -> tuple[list[str], list[str], str]:
  # create prompters
  summary_prompter = create_prompter(
    classname=params['prompter']
  ) if 'prompter' in params else SimplePrompter()
  title_prompter = create_prompter(
    classname='Title' + params['prompter']
  ) if 'prompter' in params else TitleSimplePrompter()

  # generate summaries, instructions and title
  summaries, instructions, title = proxy_summary_title(
    text='\n'.join(params['sentences']),
    title=params['title'],
    summary_prompter=summary_prompter,
    title_prompter=title_prompter,
  )

  # TODO add an option to handle title
  # Insert title to the beginning of summaries and instructions
  summaries.insert(0, title)
  instructions.insert(0, title)

  # save to file
  with open(os.path.join(params['cwd'], 'summaries.json'), 'w') as fp:
    json.dump({
      'title': title,
      'summaries': summaries,
      'instructions': instructions,
    }, fp, ensure_ascii=False, indent=2)
    fp.close()

  return summaries, instructions, title


if __name__ == '__main__':
  from utils.workflow import run_activity
  run_activity([summarize, summary_and_title], task_queue='text-summary')
