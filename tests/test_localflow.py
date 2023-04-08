# path: tests/test_localflow.py

import pytest
from unittest.mock import mock_open, patch, MagicMock

from vcg.localflow import main, parse_args


# How to mock open()
# @patch('builtins.open', MockOpen().open)
class MockOpen:
  def __init__(self, read_data=''):
    self.builtin = open
    self.mock = mock_open(read_data=read_data)

  def open(self, *args, **kwargs):
    if len(args) > 0 and args[0] == 'dummy.json':
      return self.mock(*args, **kwargs)
    return self.builtin(*args, **kwargs)


# TODO
# it seems that ArgumentParser uses gettext to do translation which
# will read 4 bytes from a file to test endian, so provide read_data
# with 4 bytes `b'data'`to avoid error
@patch('builtins.open', new_callable=mock_open, read_data=b'data')
@patch('os.path.exists')
@patch('json.load')
@patch('argparse.ArgumentParser.parse_args')
def test_parse_args(
  mock_args,
  mock_load,
  mock_exists,
  mock_file,
):
  args = MagicMock()
  args.params = 'dummy.json'

  mock_args.return_value = args
  mock_exists.return_value = False
  with pytest.raises(RuntimeError) as e:
    parse_args()
    assert 'does not exist' in str(e.value)
    assert mock_args.call_count == 1
    assert mock_exists.call_count == 1

  mock_load.return_value = {
    'cwd': '/path',
    'url': 'https://mp.weixin.qq.com/s/WRCfatBGqWzAxaV-kWEJ4Q',
    'voice_ali': 'kenny',
    'prompter': 'ScenePrompter',
  }
  mock_exists.return_value = True
  args.url = 'google.com'
  args.voice_ali = 'someone'
  args.cwd = '/nowhere'
  args.prompter = 'nobody'

  params = parse_args()

  assert params['url'] == 'google.com'
  assert params['voice_ali'] == 'someone'
  assert params['cwd'] == '/nowhere'
  assert params['prompter'] == 'nobody'
  assert mock_args.call_count == 2
  assert mock_load.call_count == 1
  mock_file.assert_any_call('dummy.json', 'rb')


@pytest.mark.asyncio
@patch('vcg.localflow.concat_video')
@patch('vcg.localflow.generate_video')
@patch('vcg.localflow.synthesize_speech')
@patch('vcg.localflow.retrieve_image')
@patch('vcg.localflow.summary_and_title')
@patch('vcg.localflow.parse_url')
async def test_localflow(
  mock_parse_url,
  mock_summary_and_title,
  mock_retrieve_image,
  mock_synthesize_speech,
  mock_generate_video,
  mock_concat_video,
  tmp_path,
  params,
):
  mock_concat_video.return_value = (
    params['output'],
    params['bgm'],
    params['kfa'],
  )
  mock_generate_video.return_value = params['videos']
  mock_synthesize_speech.return_value = (
    params['audio'],
    params['subtitles'],
  )
  mock_retrieve_image.return_value = params['frames']
  mock_summary_and_title.return_value = (
    params['summaries'],
    params['instructions'],
    params['title'],
  )
  mock_parse_url.return_value = (
    params['sentences'],
    params['images'],
    params['title'],
  )

  output = await main({
    'cwd': tmp_path,
    'url': 'a',
    'voice_ali': 'kenny',
    'prompter': 'ScenePrompter',
  })

  assert output == params['output']
  mock_parse_url.assert_called_once()
  mock_summary_and_title.assert_called_once()
  mock_retrieve_image.assert_called_once()
  mock_synthesize_speech.assert_called_once()
  mock_generate_video.assert_called_once()
  mock_concat_video.assert_called_once()


# @pytest.mark.asyncio
# @patch('vcg.videogen.activity.audio_mix')
# @patch('vcg.videogen.activity.keyframe')
# @patch('vcg.videogen.activity.concat')
# @patch('vcg.videogen.activity.generate')
# @patch('vcg.speechsynthesis.activity.tts')
# @patch('vcg.imageretrieval.activity.retrieve')
# @patch('vcg.textsummary.activity.summary_and_title')
# @patch('vcg.urlparser.activity.parse')
# async def test_parse_url(
#   mock_parse,
#   mock_summary,
#   mock_retrieve,
#   mock_tts,
#   mock_generate,
#   mock_concat,
#   mock_keyframe,
#   mock_audio_mix,
#   tmp_path,
#   params,
# ):
#   mock_audio_mix.return_value = (
#     params['output'],
#   )
#   mock_keyframe.return_value = (
#     params['videos'],
#     params['kfa'],
#   )
#   mock_concat.return_value = (
#     params['output'],
#   )
#   mock_generate.return_value = (
#     params['videos'],
#   )
#   mock_tts.return_value = (
#     params['audio'],
#   )
#   mock_retrieve.return_value = (
#     params['frames'],
#   )
#   mock_summary.return_value = (
#     params['summaries'],
#     params['instructions'],
#     params['title'],
#   )
#   mock_parse.return_value = (
#     params['sentences'],
#     params['images'],
#     {'title': params['title']},
#   )

#   output = await main({
#     'cwd': tmp_path,
#     'url': 'a',
#     'voice_ali': 'kenny',
#     'prompter': 'ScenePrompter',
#   })

#   assert output == params['output']
#   mock_parse.assert_called_once()
#   mock_summary.assert_called_once()
#   mock_retrieve.assert_called_once()
#   mock_tts.assert_called_once()
#   mock_generate.assert_called_once()
#   mock_concat.assert_called_once()
#   mock_keyframe.assert_called_once()
#   mock_audio_mix.assert_called_once()
