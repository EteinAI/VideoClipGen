# Path: vcg/storage/activity.py

import os
from urllib.parse import urlunsplit

from temporalio import activity

from utils.decorator import check_env
from .oss import upload_folder


@activity.defn(name='upload_oss')
async def upload_oss(params) -> str:
  @check_env('OSS_DOWNLOAD_ENDPOINT', 'OSS_BUCKET')
  def inner():
    print(f'Uploading {params["cwd"]} to oss...')
    upload_folder(params['cwd'])

    return urlunsplit((
      'https',
      f'{os.getenv("OSS_BUCKET")}.{os.getenv("OSS_DOWNLOAD_ENDPOINT")}',
      os.path.join(params['id'], params['output']),
      '', '',
    ))

  return inner()
