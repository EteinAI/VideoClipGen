# Path: vcg/storage/oss.py

import os
import logging

from dotenv import load_dotenv
import oss2
from pprint import pformat

from utils.decorator import check_env


load_dotenv()


@check_env(
  'OSS_ACCESSKEY_ID',
  'OSS_ACCESSKEY_SECRET',
  'OSS_UPLOAD_ENDPOINT',
  'OSS_BUCKET',
)
def upload_folder(folder_path):
  key = os.getenv('OSS_ACCESSKEY_ID')
  secret = os.getenv('OSS_ACCESSKEY_SECRET')
  endpoint = os.getenv('OSS_UPLOAD_ENDPOINT')
  bucket_name = os.getenv('OSS_BUCKET')

  bucket = oss2.Bucket(
    auth=oss2.Auth(key, secret),
    endpoint=endpoint,
    bucket_name=bucket_name,
  )
  root = os.path.abspath(os.path.join(folder_path, '..'))

  file_list = []
  for path, _, files in os.walk(folder_path):
    for file in files:
      if file.startswith('.'):
        continue
      file_path = os.path.join(path, file)
      key = os.path.relpath(file_path, root)
      file_list.append((key, file_path))

  for key, file_path in file_list:
    try:
      headers = {
        'Content-Type': 'application/octet-stream',
      } if key.endswith('.mp4') else None
      logging.info(f'Uploading {file_path} as {key} ...')
      resp = bucket.put_object_from_file(key, file_path, headers=headers)
      logging.info(pformat(vars(resp)))
    except Exception as e:
      logging.error(f'Failed to upload {key}')
      raise RuntimeError(f'Upload failed: {str(e)}')
