# Path: textsummary/summary.py

import os

from textsummary.prompts import Prompter

from dotenv import load_dotenv
load_dotenv()


# generate summaries via openai api
def openai_summary(
  text: str,
  prompter: Prompter = Prompter()
) -> tuple[list[str], list[str]]:
  import openai

  api_key = str(os.getenv('OPENAI_API_KEY'))
  if api_key == 'None':
    print('PROXY_API_KEY not found in env or in .env file')
    return [], []
  else:
    openai.api_key = api_key

  response = openai.ChatCompletion.create(
    model='gpt-3.5-turbo',
    messages=[
      {'role': 'system', 'content': 'You are a chatbot'},
      {'role': 'user', 'content': prompter.prompt(text)},
    ]
  )

  if response.choices is None or len(response.choices) == 0:
    return [], []

  answer = response.choices[0].message.content
  return prompter.summaries(answer), prompter.instructions(answer)


# generate summaries via proxy service
def proxy_summary(
  text: str,
  prompter: Prompter = Prompter()
) -> tuple[list[str], list[str]]:
  import json
  import requests
  from sseclient import SSEClient

  api_key = str(os.getenv('PROXY_API_KEY'))
  if api_key == 'None':
    print('PROXY_API_KEY not found in env or in .env file')
    return [], []

  response = requests.post(
    'https://chat.cyberytech.com/conversation',
    data=json.dumps({
      'clientOptions': {'clientToUse': 'chatgpt'},
      'message': prompter.prompt(text),
      'stream': True
    }),
    headers={
      'Accept': 'text/event-stream',
      'Accept-Encoding': 'gzip, deflate, br',
      'Authorization': 'Bearer ' + api_key,
      'Content-Type': 'application/json',
    },
    stream=True
  )
  client = SSEClient(response)
  for event in client.events():
    if event.event == 'result':
      answer = json.loads(event.data)['response']
      return prompter.summaries(answer), prompter.instructions(answer)

  return [], []
