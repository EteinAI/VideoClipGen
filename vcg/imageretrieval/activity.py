import os
import shutil

from temporalio import activity

from imageretrieval.retrieval import retrieve
from imageretrieval.retrieval import ImageEmbeddings, TextEmbeddings


@activity.defn(name='retrieve_image')
async def retrieve_image(params) -> list[list[str]]:
  selected, kept, dropped = retrieve(params['instructions'], params['images'])

  cwd = os.path.join(params['cwd'], 'retrieve')
  selected_path = os.path.join(cwd, 'selected')
  kept_path = os.path.join(cwd, 'kept')
  dropped_path = os.path.join(cwd, 'dropped')
  if not os.path.exists(cwd):
    os.makedirs(selected_path)
    os.makedirs(kept_path)
    os.makedirs(dropped_path)

  for image in kept:
    shutil.copy(image, kept_path)
  for image in dropped:
    shutil.copy(image, dropped_path)

  retrieved: list[list[str]] = []
  for images in selected:
    retrieved.append([])
    for image in images:
      new_file = shutil.copy(image, selected_path)
      retrieved[-1].append(str(new_file))

  return retrieved


if __name__ == '__main__':
  from workflow.base import run_activity

  # HACK! print model name to preloaded models
  print('Starting image retrieval activity...')
  print(f'Image embedding model: {ImageEmbeddings.instance().name}')
  print(f'Text embedding model: {TextEmbeddings.instance().name}')

  run_activity([retrieve_image], task_queue='image-retrieval')
