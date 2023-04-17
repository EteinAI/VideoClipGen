# Path: vcg/speechsynthesis/alitts.py

import logging
import json
import os
import requests
from urllib import parse

import nls
from dotenv import load_dotenv

from utils.decorator import check_env
from .subtitle import tokenize, wording, subtitle


load_dotenv()


# HACK! hardcoded system settings
auth_url = 'http://nls-meta.cn-shanghai.aliyuncs.com/'
tts_rest_url = 'https://nls-gateway.aliyuncs.com/stream/v1/tts'
tts_ws_url = 'wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1'

# HACK! hardcoded user preferences
default_voice = 'zhiyan_emo'


@check_env('ALI_ACCESSKEY_ID')
@check_env('ALI_ACCESSKEY_SECRET')
def create_token():
  import base64
  import hashlib
  import hmac
  import time
  import uuid

  data = {
    'AccessKeyId': os.getenv('ALI_ACCESSKEY_ID'),
    'Action': 'CreateToken',
    'Format': 'JSON',
    'RegionId': 'cn-shanghai',
    'SignatureMethod': 'HMAC-SHA1',
    'SignatureNonce': str(uuid.uuid1()),
    'SignatureVersion': '1.0',
    'Timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    'Version': '2019-02-28'
  }

  # 构造规范化的请求字符串
  query_string = parse.urlencode(sorted(data.items(), key=lambda x: x[0]),
                                 quote_via=parse.quote)
  # print(f'Query\n{query_string}')

  # 构造待签名字符串
  # quote_plus('/')=%2F
  string_to_sign = 'POST&%2F&' + parse.quote(query_string)
  # print(f'Sign\n{string_to_sign}')

  # 计算签名
  key = bytes(str(os.getenv('ALI_ACCESSKEY_SECRET')) + '&', encoding='utf-8')
  msg = bytes(string_to_sign, encoding='utf-8')
  secreted_string = hmac.new(key, msg, hashlib.sha1).digest()
  signature = base64.b64encode(secreted_string)
  logging.info(f'Signiture: {signature}')

  url = auth_url
  headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/x-www-form-urlencoded'
  }
  data['Signature'] = signature
  response = requests.post(url, headers=headers, data=data)
  # from pprint import pprint
  # print('Request')
  # pprint(response.request.body)
  # print('Response')
  # pprint(response.json())

  if response.ok:
    root_obj = response.json()
    token = root_obj['Token']
    if token is not None:
      logging.info(f'Ali TTS token created: {token["Id"]}')
      logging.info(f'           expires at: {token["ExpireTime"]}')
      return token['Id'], token['ExpireTime']
  return '', 0


@check_env('ALI_APP_KEY')
def tts(texts, cwd, voice=None):
  """
  Generate audio files from texts.

  Args:
    cwd: where the audio files are stored, must exist
  """

  voice = voice or default_voice

  url = tts_rest_url
  headers = {
    'Content-Type': 'application/json',
  }
  data = {
    'appkey': os.getenv('ALI_APP_KEY'),
    'token': create_token()[0],
    'sample_rate': 16000,
    'voice': voice,
    'format': 'wav'
  }

  wav_files = []
  for idx, text in enumerate(texts):
    data['text'] = text
    response = requests.post(
      url=url,
      headers=headers,
      data=json.dumps(data)
    )
    if response.ok:
      file = os.path.join(cwd, f'{idx}.wav')
      with open(file, 'wb') as f:
        for chunk in response.iter_content(1024):
          f.write(chunk)
      wav_files.append(file)

  return wav_files


def tts_with_subtitle(texts: list[str], cwd: str, voice: str | None):
  """Generate audio files from texts.

  Args:
      texts (list[str]): texts to generate wave files
      cwd (str): where the audio files are stored, must exist
      voice (str | None): voice to use, default to zhiyan_emo

  Returns:
      list[tuple(str, str)]: path to wav file and ssa file
  """

  token = create_token()[0]
  resp = [websocket_tts(
    text=text,
    voice=voice or default_voice,
    wav_file=os.path.join(cwd, f'{idx}.wav'),
    token=token,
  ) for idx, text in enumerate(texts)]

  wav_files = []
  ssa_files = []
  for idx, (wav_file, metadata) in enumerate(resp):
    ssa_file = os.path.join(cwd, f'{idx}.ssa')
    meta_file = os.path.join(cwd, f'{idx}.json')

    with open(meta_file, 'w') as fp:
      json.dump(metadata, fp, indent=2, ensure_ascii=False)

    tokens = tokenize(
      ts=metadata['payload']['subtitles'],
      sentence=texts[idx],
    )
    lines = wording(tokens)
    subtitles = subtitle(lines, (720, 1280))

    subtitles.save(ssa_file)
    ssa_files.append(ssa_file)
    wav_files.append(wav_file)

  return wav_files, ssa_files


@check_env('ALI_APP_KEY')
def websocket_tts(text, voice, wav_file, token):
  '''
  TTS via websocket, with subtitles(timestamps of words)
  '''

  if not token:
    raise ValueError('Token is required for websocket tts.')

  metadata = ''

  def update_metadata(data):
    nonlocal metadata
    metadata = data

  def on_error(message, *args):
    logging.error(f'TTS error with args {args}')
    raise RuntimeError(message)

  print(f'Generating {wav_file}...')
  with open(wav_file, 'wb') as f:
    tts = nls.NlsSpeechSynthesizer(
      url=tts_ws_url,
      token=token,
      appkey=os.getenv('ALI_APP_KEY'),
      on_metainfo=update_metadata,
      on_data=lambda x: f.write(x),
      on_error=on_error,
      on_close=lambda: print('TTS closed'),
      on_completed=lambda: print('TTS completed'),
    )
    tts.start(
      text,
      aformat='wav',
      sample_rate=44100,
      voice=voice,
      ex={
        'enable_subtitle': True,
        # 'enable_phoneme_timestamp': True,
      }
    )
    f.close()

  if metadata == '':
    raise RuntimeError(f'No metadata received for {wav_file}')

  print(f'Done with {wav_file}...')

  return wav_file, json.loads(metadata)


# class WSTTS:
#   def __init__(self, tid):
#     self.__th = threading.Thread(target=self.__test_run)
#     self.__id = tid

#   def start(self, text, audio_file):
#     self.__text = text
#     self.__audio_file = audio_file
#     # self.__meta_file = audio_file + ".json"

#     self.__f = open(self.__audio_file, "wb")
#     self.__th.start()
#     self.__th.join()
#     return self.__metadata

#   def test_on_metainfo(self, message, *args):
#     # print("on_metainfo message=>{}".format(message))
#     self.__metadata = message

#   def test_on_error(self, message, *args):
#     print("on_error args=>{}".format(args))

#   def test_on_close(self, *args):
#     print("on_close: args=>{}".format(args))
#     try:
#       self.__f.close()
#     except Exception as e:
#       print("close file failed since:", e)

#   def test_on_data(self, data, *args):
#     try:
#       self.__f.write(data)
#     except Exception as e:
#       print("write data failed:", e)

#   def test_on_completed(self, message, *args):
#     print("on_completed:args=>{} message=>{}".format(args, message))

#   def __test_run(self):
#     print("thread:{} start..".format(self.__id))
#     tts = nls.NlsSpeechSynthesizer(
#       url="wss://nls-gateway.aliyuncs.com/ws/v1",
#       token=create_token()[0],
#       appkey=os.getenv('ALI_APP_KEY'),
#       on_metainfo=self.test_on_metainfo,
#       on_data=self.test_on_data,
#       on_completed=self.test_on_completed,
#       on_error=self.test_on_error,
#       on_close=self.test_on_close,
#       callback_args=[self.__id],
#     )
#     print("{}: session start".format(self.__id))
#     r = tts.start(
#       self.__text,
#       aformat='wav',
#       sample_rate=44100,
#       voice=default_voice,
#       ex={
#         'enable_subtitle': True,
#         'enable_phoneme_timestamp': True,
#       }
#     )

#     print("{}: tts done with result:{}".format(self.__id, r))
