# Path: videogen/ffmpegcli.py

import ffmpeg
import os
import subprocess

from pprint import pprint


def generate(assets, cwd, verbose=False):
  """
  Generate videos from frames and audio.
  """

  videos = []
  for i, asset in enumerate(assets):
    path = os.path.join(cwd, f'{i}.mp4')

    video = ffmpeg.input(asset['frames'][0]).video
    audio = ffmpeg.input(asset['audio']).audio.filter(
      # extend(padding) audio by 0.5s to make the concatenation more natural
      'apad',
      pad_dur=0.5,
    ).filter(
      'aformat',
      sample_fmts='fltp',
      sample_rates=44100,
    )

    stream = ffmpeg.concat(video, audio, v=1, a=1, n=2).filter(
      'crop',
      w='trunc(iw/2)*2',
      h='trunc(ih/2)*2',
    ).output(
      path,
      r=24,  # set fps explicitly to support gif
      vcodec='libx264',
      acodec='aac',
      pix_fmt='yuvj420p',
      strict='experimental',
    )
    args = stream.compile()
    process = subprocess.Popen(
      args,
      stderr=subprocess.PIPE,
      stdout=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()
    if verbose:
      print(stdout.decode('utf-8'))
    if process.returncode != 0:
      pprint(args)
      print(stderr.decode('utf-8'))
    else:
      print(f'Video clip: {path}')
      videos.append(path)

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
  stream = ffmpeg.concat(*filter_graphs, v=1, a=1).output(output)

  args = stream.compile()
  process = subprocess.Popen(args, stderr=subprocess.PIPE)
  _, stderr = process.communicate()
  if process.returncode != 0:
    pprint(args)
    print(stderr.decode('utf-8'))
    return ''
  else:
    print(f'Video clips concated: {output}')
    return output


def audio_mix(video_file, bgm_file, output, volume_level='-20dB'):
  """
  Add background music to video.
  """

  input = ffmpeg.input(video_file)

  stereo = ffmpeg.filter(
    (input.audio, input.audio),
    'amerge',
    inputs=2,
  )
  bgm = ffmpeg.input(
    bgm_file,
    stream_loop=-1
  ).filter(
    'volume',
    volume=volume_level,
  )

  # Merge audio streams
  merged_audio = ffmpeg.filter(
    (stereo, bgm),
    'amerge',
    inputs=2,
  )
  stream = ffmpeg.concat(
    input.video,
    merged_audio,
    v=1, a=1, n=2,
  ).output(
    output,
    ac=2,
    acodec='aac',
    strict='experimental',
  )

  args = stream.compile()
  process = subprocess.Popen(args, stderr=subprocess.PIPE)
  _, stderr = process.communicate()
  if process.returncode != 0:
    pprint(args)
    print(stderr.decode('utf-8'))
    return ''
  else:
    print(f'Background music added: {output}')
    return output
