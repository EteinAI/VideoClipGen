import base64
import hashlib
import hmac
import json
import os
import requests
import time
import uuid
from urllib import parse

from dotenv import load_dotenv

load_dotenv()


def create_token():
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
  print(f'Signiture: {signature}')

  url = 'http://nls-meta.cn-shanghai.aliyuncs.com/'
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
      return token['Id'], token['ExpireTime']
  return None, None


def tts(texts, cwd, voice=None):
  """
  Generate audio files from texts.

  Args:
    cwd: where the audio files are stored, must exist
  """

  if voice is None:
    voice = 'zhiyan_emo'

  url = 'https://nls-gateway.aliyuncs.com/stream/v1/tts'
  headers = {'Content-Type': 'application/json'}
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
