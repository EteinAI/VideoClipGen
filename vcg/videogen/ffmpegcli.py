# Path: videogen/ffmpegcli.py

import ffmpeg
import os
import subprocess
import logging

from videogen.keyframe import kfa


# shared ffmpeg command line parameters
# https://ffmpeg.org/ffmpeg.html#Options
# video: https://trac.ffmpeg.org/wiki/Encode/H.264
vconf = {
  'crf': 20,
  'tune': 'stillimage',
  'vcodec': 'libx264',
  'pix_fmt': 'yuvj420p',
  'vprofile': 'high',
}
# audio: https://trac.ffmpeg.org/wiki/Encode/AAC
aconf = {
  'acodec': 'aac',
  'ac': 2,
}
# output
oconf = {
  'strict': 'strict',
}

default_size = (720, 1280)


def duration(file) -> float:
  """
  Get the duration of a video/audio file in seconds.
  """
  probe = ffmpeg.probe(file)
  return max([float(s['duration']) for s in probe['streams']
              if s['duration'] is not None])


def size(file) -> tuple[int, int]:
  """
  Get the resolution of a video file in pixels
  """
  probe = ffmpeg.probe(file)
  vstream = next((s for s in probe['streams']
                 if s['codec_type'] == 'video'), None)
  if vstream is None:
    raise RuntimeError(f'ffprobe: No video stream found in {file}')

  return int(vstream['width']), int(vstream['height'])


def run(stream, verbose=False):
  """
  Run a ffmpeg command with subprocess.
  Log error if return code is not 0, log stdout if verbose is True.
  """
  args = stream.overwrite_output().compile()
  process = subprocess.Popen(
    args,
    stderr=subprocess.PIPE,
    stdout=subprocess.PIPE,
  )
  stdout, stderr = process.communicate()
  if verbose:
    logging.warning(stdout.decode('utf-8'))
  if process.returncode != 0:
    logging.error(args)
    logging.error(stderr.decode('utf-8'))
  return process.returncode


def generate(assets, cwd, extend=0.5, verbose=False):
  """
  Generate videos from frames and audio.
  assets = [
    {'frames': [frame1, frame2, ...], 'audio': audio},
    {'frames': [frame1, frame2, ...], 'audio': audio},
    ...
  ]
  output = [
    '1.mp4',
    '2.mp4',
     ...
  ]
  """

  videos = []
  for i, asset in enumerate(assets):
    path = os.path.join(cwd, f'{i}.mp4')

    video = ffmpeg.input(
      asset['frames'][0],
      r=25,  # set fps explicitly to support gif
      loop=1,
      t=duration(asset['audio']) + extend,
    ).video.filter(
      'crop',
      w='trunc(iw/2)*2',
      h='trunc(ih/2)*2',
    )

    audio = ffmpeg.input(asset['audio']).audio.filter(
      # extend(padding) audio by extend to make the concatenation more natural
      'apad',
      pad_dur=extend,
    ).filter(
      # convert audio to float format with sample rate 44.1kHz
      'aformat',
      sample_fmts='fltp',
      sample_rates=44100,
    )

    stream = ffmpeg.concat(
      video, audio,
      v=1, a=1, n=2,
    ).output(
      path,
      **vconf, **aconf, **oconf,
      shortest=None,
    )

    if run(stream, verbose=verbose) == 0:
      logging.info(f'Video clip: {path}')
      videos.append(path)

  return videos


def keyframe(videos, cwd, verbose=False):
  """
  Add keyframe animation to videos
  videos = [
    '1.mp4',
    '2.mp4',
    ...
  ]
  output = [
    '1_kfa.mp4',
    '2_kfa.mp4',
    ...
  ]
  """

  kfa_names = []
  kfa_videos = []
  for src in videos:
    input = ffmpeg.input(src)
    output = os.path.join(cwd, f'{os.path.basename(src)}_kfa.mp4')

    s = size(src)
    video, name = kfa(input.video, size=s, duration=duration(src))
    stream = ffmpeg.output(
      video, input.audio,
      output, **vconf, **aconf, **oconf,
    )

    if run(stream, verbose=verbose) == 0:
      logging.info(f'Add keyframe animation {name} to video{s}: {src}')
      kfa_videos.append(output)
      kfa_names.append(name)

  return kfa_videos, kfa_names


def concat(videos, output, subtitles=None, size=None, verbose=False):
  """
  Concatenate videos.
  Scale and pad the videos to the same size, then concatenate them.
  """

  width, height = size or default_size

  if subtitles is not None and len(videos) != len(subtitles):
    raise ValueError('The number of videos and subtitles must be the same')

  filter_graphs = []
  for i, file in enumerate(videos):
    input = ffmpeg.input(file)
    video = input.video.filter(
      'scale',
      w=f'{width}',
      h='-2',
    ).filter(
      'pad',
      w=f'{width}',
      h=f'{height}',
      x='(ow-iw)/2',
      y='(oh-ih)/2',
      color='black',
    ).filter(
      'setsar',
      r='1',
      max='1'
    )
    if subtitles is not None:
      video = video.filter(
        'subtitles',
        f=subtitles[i],
      )
    filter_graphs.append(video)
    filter_graphs.append(input.audio)

  try:
    stream = ffmpeg.concat(*filter_graphs, v=1, a=1).output(
      output, **vconf, **aconf, **oconf,
    )
  except Exception as e:
    logging.error(str(e))
    raise RuntimeError(f'Failed to assemble stream: {output}')

  if run(stream, verbose=verbose) != 0:
    raise RuntimeError(f'Failed to concatenate videos: {output}')

  logging.info(f'Video clips concatenated: {output}')

  return output


def audio_mix(video_file, bgm_file, output,
              verbose=False, bgm_volume='-20dB'):
  """
  Add background music to video.
  """

  input = ffmpeg.input(video_file)

  bgm = ffmpeg.input(
    bgm_file,
    stream_loop=-1
  ).filter(
    'volume',
    volume=bgm_volume,
  )

  # Merge audio streams
  merged_audio = ffmpeg.filter(
    (input.audio, bgm),
    'amerge',
    inputs=2,
  )
  stream = ffmpeg.concat(
    input.video,
    merged_audio,
    v=1, a=1, n=2,
  ).output(
    output,
    # can not use vcodec='copy' here
    # FFmpeg: Filtering and streamcopy cannot be used together
    **vconf, **aconf, **oconf
  )

  if run(stream, verbose=verbose) != 0:
    raise RuntimeError(f'Failed to add background music to {video_file}')

  logging.info(f'Background music mixed: {output}')

  return output
