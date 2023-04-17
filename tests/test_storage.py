

from vcg.storage.oss import upload_folder


def test_oss_upload_folder(workspace):
  upload_folder(workspace)
