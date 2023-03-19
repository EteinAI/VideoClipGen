# Path: textsummary/summary.py

import openai
import os
import re
from pprint import pprint

from dotenv import load_dotenv

load_dotenv()

template = ' TL;DR 请以 {} 句话为以上文字提供摘要，要求不少于 {} 字，不超过 {} 字, 每句话 {} 字左右，并且以"。"结束，以中文作答，最后一句不使用总结的口吻'

# generate summaries via openai api


def openai_summary(
  texts: str,
  min=200,
  max=250,
  sentence_count=6,
  sentence_length=40
) -> list[str]:
  openai.api_key = os.getenv('OPENAI_API_KEY')

  prompt = '\n'.join([texts, template.format(
    sentence_count, min, max, sentence_length)])
  print('prompt:', prompt)

  response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
      {"role": "system", "content": "You are a chatbot"},
      {"role": "user", "content": prompt},
    ]
  )
  pprint(response)

  # TODO check length of summaries, retry if requirements not met
  summaries = [s for s in re.split(
    r'。|；', response.choices[0].message.content) if len(s) > 0]
  pprint(summaries)

  return summaries

# generate summaries via proxy service


def proxy_summary(
  texts: str,
  min=200,
  max=250,
  sentence_count=6,
  sentence_length=40
) -> list[str]:
  import json
  import requests
  from sseclient import SSEClient

  prompt = '\n'.join([texts, template.format(
    sentence_count, min, max, sentence_length)])
  print('prompt:', prompt)

  response = requests.post(
    'https://chat.cyberytech.com/conversation',
    data=json.dumps({
      'clientOptions': {'clientToUse': 'chatgpt'},
      'message': prompt,
      'stream': True
    }),
    headers={
      'Accept': 'text/event-stream',
      'Accept-Encoding': 'gzip, deflate, br',
      'Authorization': 'Bearer ' + str(os.getenv('PROXY_API_KEY')),
      'Content-Type': 'application/json',
    },
    stream=True
  )
  client = SSEClient(response)
  for event in client.events():
    if event.event == 'result':
      answer = json.loads(event.data)['response']
      # TODO check length of summaries, retry if requirements not met
      summaries = [s for s in re.split(r'。|；', answer) if len(s) > 0]
      pprint(summaries)

      return summaries
  return []
