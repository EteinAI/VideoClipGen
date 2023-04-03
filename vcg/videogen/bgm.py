# path vcg/videogen/bgm.py

import os
from pathlib import Path


class BGM:
  """
  A class that manages background music files.
  """

  def __init__(self, path=None):
    root = path if path is not None else os.getenv('VCG_BGM_ROOT')
    if root is None:
      raise RuntimeError(
        'BGM root dir not specified, nor in env (VCG_BGM_ROOT)')
    if not os.path.exists(root):
      raise RuntimeError(f'BGM root dir not exists: {root}')
    self._root = Path(root)
    self._bgms = {os.path.basename(f): str(f) for f in [
      *self._root.glob('**/*.m4a'),
      *self._root.glob('**/*.mp3'),
      *self._root.glob('**/*.wav'),
    ]}

  def __len__(self):
    return len(self._bgms)

  def __getitem__(self, key):
    return self._bgms[key]

  def __contains__(self, item):
    return item in self._bgms

  def all(self):
    return list(self._bgms.keys())

  def random(self):
    import random
    if len(self._bgms) == 0:
      return '', ''
    key = random.choice(list(self._bgms.keys()))
    return key, self._bgms[key]

  _singleton = None

  @classmethod
  def instance(cls):
    if BGM._singleton is None:
      BGM._singleton = BGM()
    return BGM._singleton
