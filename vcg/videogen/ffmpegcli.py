# Path: videogen/ffmpegcli.py

import ffmpeg
import os


def generate(assets, cwd):
  """
  Generate videos from frames and audio.
  """

  videos = []
  for i, asset in enumerate(assets):
    path = os.path.join(cwd, f'{i}.mp4')
    videos.append(path)

    a = ffmpeg.input(asset['audio'])
    v = ffmpeg.input(asset['frames'][0])
    stream = ffmpeg.concat(
      v.video,
      a.audio,
      v=1,
      a=1
    ).filter(
      'crop',
      w='trunc(iw/2)*2',
      h='trunc(ih/2)*2'
    ).output(
      path,
      vcodec='libx264',
      acodec='aac',
      pix_fmt='yuvj420p',
      strict='experimental'
    )
    print(stream.compile())
    stream.run(
      capture_stdout=True,
      overwrite_output=True
    )

  return videos


def concat(videos, output, width=720, height=1280):
  """
  Concatenate videos.
  Scale and pad the videos to the same size, then concatenate them.
  """

  filter_graphs = []
  for file in videos:
    input = ffmpeg.input(file)
    filter_graphs.append(input.video.filter(
      'scale',
      width=f'{width}',
      height='-2',
    ).filter(
      'pad',
      width=f'{width}',
      height=f'{height}',
      x='(ow-iw)/2',
      y='(oh-ih)/2',
      color='black',
    ).filter(
      'setsar',
      r='1',
      max='1'
    ))
    filter_graphs.append(input.audio)

  stream = ffmpeg.concat(*filter_graphs, v=1, a=1, n=2).output(output)
  print(stream.compile())

  try:
    stream.run(
      capture_stdout=True,
      overwrite_output=True
    )
    return output
  except ffmpeg.Error as e:
    print(e.stderr.decode())
  return ''
