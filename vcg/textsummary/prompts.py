import re


class Prompter:
  def __init__(self):
    pass

  def prompt(self, text: str) -> str:
    '''
    Generate prompt for chatbot
    '''
    return text

  def instructions(self, response: str) -> list[str]:
    '''
    Parse response from chatbot, generate instructions for image retrieval
    '''
    return response.split('\n')

  def summaries(self, response: str) -> list[str]:
    '''
    Parse response from chatbot, generate summaries
    '''
    return response.split('\n')


class SimplePrompter(Prompter):
  def __init__(self, min=200, max=250, num_sentence=6, sentence_length=40):
    super().__init__()
    self._template = '''{text}
TL;DR 请为以上字提供摘要，要求如下:
1. 摘要以中文作答;
2. 摘要不少于 {min} 字，不超过 {max} 字;
3. 摘要包含 {num_sentence} 句话, 每句话 {sentence_length} 字左右
4. 摘要中每句话以中文句号作为每句话的结束;
5. 摘要中不要包含无关文字, 最后一句摘要不使用总结的口吻;
'''.format(
      text='{text}',
      min=min,
      max=max,
      num_sentence=num_sentence,
      sentence_length=sentence_length
    )

  def prompt(self, text: str) -> str:
    return self._template.format(text=text)

  def instructions(self, response: str) -> list[str]:
    return [s for s in re.split(r'。|；', response) if len(s) > 0]

  def summaries(self, response: str) -> list[str]:
    return self.instructions(response)


class ScenePrompter(Prompter):
  def __init__(self, num_scene=6, num_keyword=1, sentence_length=40):
    super().__init__()
    self._template = '''{text}
我想根据这段文字做一个营销短视频，作为营销大师，请帮我设计出{num_scene}个适合短视频的场景。
每个场景提炼{num_keyword}个关键词，再写{sentence_length}个字左右的抖音风格文案。
其中第一个场景是整体介绍，不要出现原文中没有的地名和产品名。
请使用中文输出，输出时的格式为: "场景:, 关键词:, 文案:"。
输出时请直接给出结果，不要包含无关语句。'''.format(
      text='{text}',
      num_scene=num_scene,
      num_keyword=num_keyword,
      sentence_length=sentence_length
    )

  def prompt(self, text: str) -> str:
    return self._template.format(text=text)

  def instructions(self, resp: str) -> list[str]:
    return ['场景' + s.strip() for s in resp.split('场景') if len(s.strip()) > 0]

  def summaries(self, resp: str) -> list[str]:
    return [re.split(r':|：', s)[-1].strip() for s in self.instructions(resp)]