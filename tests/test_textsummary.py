# Path tests/test_textsummary.py

import pytest

from vcg.textsummary.summary import proxy_summary, proxy_summary_title
from vcg.textsummary.generator import Generator
from vcg.textsummary.prompts import SimplePrompter, TitleSimplePrompter
from vcg.textsummary.prompts import ScenePrompter, TitleScenePrompter


@pytest.fixture
def article():
  return '''
    软装设计，是设计一种生活方式，创造一种更为舒适的生活状态。
    无需刻意新奇，无关美丑新旧，只为营造家的舒适感，对空间的归属感，以及身心愉悦的装饰氛围。
    本期方案，利用干净的配色、明晰的线条、丰富的造型，以及充足的采光，让空间充满元气，生活充满幸福感。
    客餐厅一体化设计，空间开阔感极大提升。简约的无主灯设计，灯带与筒灯实现均匀照明与局部重点照明，更具氛围感。
    客餐厅两侧窗户大面积自然采光，则让空间时刻充满自然气息。
    客餐厅配色以无彩色为主，浅灰色搭配棕灰色的大面积墙体，干净简洁。肤感膜、细格栅与波浪板的应用，则让空间材质与造型更为丰富。
    黑色金属线条的加入，能灵活地设计墙咔布局与造型，金属质感，时尚精致，令装饰的灵动感与趣味性更上一层。
    窗帘采用拼色款，与木纹墙咔的棕灰色相呼应，色彩和谐的同时，良好的遮光性与垂顺度，进一步提升空间舒适度与美感。
    主卧延续整体的设计风格，大面积无彩色干净简洁的基调下，利用木纹墙咔的棕色系，加以点缀。
    床体选用质感十足的绒面材质，柔软温和，棕色系的加持，更让舒适指数大为提升。
    壁上观背景以及床头挂画，作为点睛之笔，赋予空间时尚艺术性。
    整体给人的感觉，在现代简约之下，有一点点复古怀旧，一点点清新自然。
    儿童房的打造，则是在原有风格的基础上，点缀了充满生机的绿色。床头挂画与懒人沙发，深绿色装饰清新自然。
    衣柜则是淡淡的湖水绿，让空间的氛围更加轻松，整体是现代与森系结合的舒适空间。
    为 YAKINO 雅琪诺点赞。
  '''


@pytest.mark.parametrize('prompter', [
  SimplePrompter(),
  ScenePrompter(),
])
def test_proxy_summary(article, prompter):
  summary = proxy_summary(article, prompter)
  assert len(summary) > 0


@pytest.mark.parametrize('prompter', [
  SimplePrompter(),
  ScenePrompter(),
])
def test_generator(article, prompter):
  gen1 = Generator()
  resp = gen1.query(article, prompter)
  assert len(resp) > 0
  gen2 = Generator(gen1)
  resp = gen2.query(resp, prompter)
  assert len(resp) > 0


@pytest.mark.parametrize('prompters', [
  (SimplePrompter(), TitleSimplePrompter()),
  (ScenePrompter(), TitleScenePrompter())
])
def test_summary_and_title(article, prompters):
  summaries, instructions, title = proxy_summary_title(
    text=article,
    summary_prompter=prompters[0],
    title_prompter=prompters[1],
  )
  assert len(summaries) > 0
  assert len(instructions) > 0
  assert title != ''
