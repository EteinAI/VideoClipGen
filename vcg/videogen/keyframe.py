# Path: videogen/keyframe.py

import random


class KeyFrame:
  """
  base class for keyframe animation.
  """

  def __init__(self, fc, fps, zoom, duration):
    self._fc = fc
    self._fps = fps
    self._zoom = zoom
    self._duration = duration

  def __call__(self, input, size, duration=None):
    pass

  @property
  def name(self):
    return 'keyframe'


class PanH(KeyFrame):
  """
  Pan horizontally effect (left/right)
  """

  left_to_right = 'min((iw-iw/zoom)/({duration}*2)*ot,(iw-iw/zoom)/2)'
  right_to_left = 'max((iw-iw/zoom)*(0.5-ot/({duration}*2)),0)'

  def __init__(self, start_from='left',
               fc=1, fps=25, zoom=1.3, duration=2.0):
    super().__init__(fc, fps, zoom, duration)
    self._start_from = start_from
    self._x = self.left_to_right if start_from == 'left' else self.right_to_left
    self._y = '(ih-ih/zoom)/2'

  def __call__(self, input, size, duration=None):
    w, h = size
    d = duration or self._duration
    return input.filter(
      # HACK scale to 5 times of the original size to avoid shaky zooming
      #  https://trac.ffmpeg.org/ticket/4298
      'scale',
      w=w * 5,
      h=-2,
    ).filter(
      'zoompan',
      fps=self._fps,
      d=self._fc,
      s=f'{w}x{h}',
      z=self._zoom,
      x=self._x.format(duration=d),
      y=self._y,
    )

  @property
  def name(self):
    return f'pan_{self._start_from}'


class Zoom(KeyFrame):
  """
  Zoom in/out effect
  """

  _zoom_in = 'min(1+{speed}*ot, {zoom})'
  _zoom_out = 'max({zoom}-{speed}*ot, 1)'

  def __init__(self, effect='in',
               fc=1, fps=25, zoom=1.1, duration=1.0):
    super().__init__(fc, fps, zoom, duration)
    self._effect = effect
    self._z = self._zoom_in if effect == 'in' else self._zoom_out

  def __call__(self, input, size, duration=None):
    w, h = size
    d = duration or self._duration
    speed = round((self._zoom - 1.0) / d, 3)
    return input.filter(
      # HACK scale to 5 times of the original size to avoid shaky zooming
      #  https://trac.ffmpeg.org/ticket/4298
      'scale',
      w=w * 5,
      h=-2,
    ).filter(
      'zoompan',
      fps=self._fps,
      d=self._fc,
      s=f'{w}x{h}',
      z=self._z.format(speed=speed, zoom=self._zoom),
      x='(iw-iw/zoom)/2',
      y='(ih-ih/zoom)/2'
    )

  @property
  def name(self):
    return f'zoom_{self._effect}'


def kfa(input, size: tuple[int, int], duration=None, name=None):
  """
  Add keyframe animation to video.
  """
  panleft = PanH(zoom=1.3, start_from='left')
  panright = PanH(zoom=1.3, start_from='right')
  zoomin = Zoom(zoom=1.5, effect='in')
  zoomout = Zoom(zoom=1.5, effect='out')

  ratio = size[0] / size[1]
  candidates = [panleft, panright, panleft, panright,  # more chances for pan
                zoomin, zoomout] if ratio > 1.3 else [zoomin, zoomout]

  effect = (
    random.choice(candidates) if name is None else
    next(effect for effect in candidates if effect.name == name)
  )
  if effect is None:
    raise ValueError(f'Invalid keyframe animation name: {name}')

  return effect(input, duration=duration, size=size), effect.name
