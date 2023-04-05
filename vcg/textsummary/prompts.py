import re


class Prompter:
  def __init__(self):
    pass

  def prompt(self, text: str) -> str:
    '''
    Generate prompt for chatbot
    '''
    return text

  def transform(self, response: str):
    '''
    Transform response from chatbot to desired format
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

  def transform(self, response: str):
    instructions = self.instructions(response)
    return instructions, instructions

  def instructions(self, response: str) -> list[str]:
    return [s for s in re.split(r'。|；', response) if len(s) > 0]

  def summaries(self, response: str) -> list[str]:
    return self.instructions(response)


class TitleSimplePrompter(Prompter):
  def __init__(self, length=20):
    super().__init__()
    self._template = '''
结合之前的文章和摘要，帮我生成一个花哨的营销视频标题，标题为中文，注意字数限制在{length}字以内
'''.format(length=length)

  def prompt(self, _: str) -> str:
    return self._template.format()

  def transform(self, response: str) -> str:
    return response


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

  def transform(self, response: str):
    instructions = ['场景' + s.strip()
                    for s in response.split('场景') if len(s.strip()) > 0]
    summaries = [re.split(r':|：', s)[-1].strip() for s in instructions]
    return summaries, instructions

  def instructions(self, resp: str) -> list[str]:
    return ['场景' + s.strip() for s in resp.split('场景') if len(s.strip()) > 0]

  def summaries(self, resp: str) -> list[str]:
    return [re.split(r':|：', s)[-1].strip() for s in self.instructions(resp)]


class TitleScenePrompter(Prompter):
  def __init__(self):
    super().__init__()
    self._template = '''{text}
这是一篇文章的标题, 请将这句话重新输出, 需求如下:
- 完整保留其中的主要部分(如中文汉字)
- 保持语义完整, 不要去除年份, 人名, 地名, 产品名等
- 去掉次要部分, 比如括号以及括号中的内容
- 不要改写, 不要增加额外内容, 不要增加额外的标点符号
标题:
'''.format(text='{text}')

  def prompt(self, text: str) -> str:
    return self._template.format(text=text)

  def transform(self, response: str) -> str:
    return response
