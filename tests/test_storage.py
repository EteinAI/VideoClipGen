

from vcg.storage.oss import upload_folder


def test_oss_upload_folder(workspace):
  path = '/Users/zhengt/Codes/VideoClipGen/data/7a48c66e-71c7-4ffe-aec9-f014b29c1cfd'
  upload_folder(path)
