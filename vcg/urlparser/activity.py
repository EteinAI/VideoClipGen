
from temporalio import activity

from urlparser.parser import parse


@activity.defn(name='parse_url')
async def parse_url(params) -> tuple[list[str], list[str]]:
  url = params['url']
  cwd = params['cwd']
  texts, images, _ = parse(url, cwd)
  return texts, images


if __name__ == '__main__':
  from workflow.base import run_activity
  run_activity([parse_url], task_queue='url-parser')
