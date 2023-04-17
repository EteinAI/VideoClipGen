

from vcg.storage.oss import upload_folder
from vcg.storage.redis import create_client


def test_oss_upload_folder(workspace):
  upload_folder(workspace)


def test_redis():
  with create_client() as client:
    assert client.ping() is True
