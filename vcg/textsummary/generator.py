
import os
import json
import requests
from sseclient import SSEClient

from textsummary.prompts import Prompter

from dotenv import load_dotenv
load_dotenv()


class Generator():
  def __init__(self, pickup=None):
    self._api_key = str(os.getenv('PROXY_API_KEY'))
    if self._api_key == 'None':
      raise RuntimeError('PROXY_API_KEY not found in env or in .env file')

    if (pickup is not None):
      self._conversation_id = pickup._conversation_id
      self._messages = pickup._messages
      self._responses = pickup._responses
    else:
      self._conversation_id = None
      self._messages = []
      self._responses = []

  def query(self,
            text: str,
            prompter: Prompter = Prompter()
            ) -> str:
    response = requests.post(
      'https://chat.cyberytech.com/conversation',
      data=json.dumps({
        'clientOptions': {'clientToUse': 'chatgpt'},
        'conversationId': self._conversation_id,
        'message': prompter.prompt(text),
        'parentMessageId': self._messages[-1] if len(self._messages) > 0 else '',
        'stream': True
      }),
      headers={
        'Accept': 'text/event-stream',
        'Accept-Encoding': 'gzip, deflate, br',
        'Authorization': 'Bearer ' + self._api_key,
        'Content-Type': 'application/json',
      },
      stream=True
    )
    client = SSEClient(response)
    for event in client.events():
      if event.event == 'result':
        result = json.loads(event.data)
        self._conversation_id = result['conversationId']
        self._responses.append(result['response'])
        self._messages.append(result['messageId'])
        return result['response']
    return ''
