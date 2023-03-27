import asyncio
import argparse

from temporalio.client import Client
from temporalio.worker import Worker


async def main(server: str, task_queue: str, activities):
  print(f'Server: {server}')
  print(f'Task queue: {task_queue}')

  # Create client connected to server at the given address
  client = await Client.connect(server)

  # Run the worker
  worker = Worker(client, task_queue=task_queue, activities=activities)
  await worker.run()


def run_activity(activities, task_queue='default'):
  parser = argparse.ArgumentParser()
  parser.add_argument('--server', default='localhost:7233')
  parser.add_argument('--task-queue')
  args = parser.parse_args()
  server = args.server
  task_queue = args.task_queue if args.task_queue is not None else task_queue

  asyncio.run(main(server, task_queue, activities))
