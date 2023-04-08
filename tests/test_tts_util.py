# Path: tests/test_tts_util.py

import pytest


from vcg.speechsynthesis.utils import (
  has_left_punct,
  has_sent_sep,
  split_sent_sep,
  remove_punct,
  replace_sent_sep,
)


@pytest.mark.parametrize('text, expected', [
  ('！a. b。 c？', 'abc'),
])
def test_remove_punct(text, expected):
  assert remove_punct(text) == expected


@pytest.mark.parametrize('text, expected', [
  ('a､b', 'a､b'),
  ('a、b', 'a、b'),
  ('a：b', 'a：b'),
  ('a；b', 'a\\nb'),
  ('a，b', 'a\\nb'),
  ('a；b', 'a\\nb'),
  ('a？b', 'a\\Nb'),
  ('a！b', 'a\\Nb'),
  ('a。b', 'a\\Nb'),
  ('a…b', 'a\\Nb'),
  ('a……b', 'a\\Nb'),
  ('a...b', 'a\\Nb'),
  ('a....b', 'a\\Nb'),
  ('a.....b', 'a\\Nb'),
  ('a......b', 'a\\Nb'),
  ('a？”b', 'a\\Nb'),
  ('a！”b', 'a\\Nb'),
  ('a。”b', 'a\\Nb'),
])
def test_replace_sent_sep(text, expected):
  assert replace_sent_sep(text) == expected


@pytest.fixture
def left_punct_pairs(request):
  return [
    (f'{request.param}', True),
    (f'{request.param}b', True),
    (f'a{request.param}', False),
    (f'a{request.param}b', False),
  ]


@pytest.mark.parametrize(
  'left_punct_pairs',
  '“‘（［｛〔《「『【〖〘〚〝﹙﹛﹝',
  indirect=True,
)
def test_has_left_punct(left_punct_pairs):
  for text, expected in left_punct_pairs:
    assert has_left_punct(text) == expected


@pytest.fixture
def sent_sep_true_pairs(request):
  return [
    (f'{request.param}', True),
    (f'{request.param}a', True),
    (f'a{request.param}', True),
    (f'a{request.param}b', False),
  ]


@pytest.mark.parametrize(
  'sent_sep_true_pairs',
  [r'。', r'！', r'？', r'\\n', r'\\N'],
  indirect=True,
)
def test_has_sent_sep_true(sent_sep_true_pairs):
  print(sent_sep_true_pairs)
  for text, expected in sent_sep_true_pairs:
    assert has_sent_sep(text) == expected


@pytest.fixture
def sent_sep_false_pairs(request):
  return [
    (f'{request.param}', False),
    (f'{request.param}a', False),
    (f'a{request.param}', False),
    (f'a{request.param}b', False),
  ]


@pytest.mark.parametrize(
  'sent_sep_false_pairs',
  '､、：；，',
  indirect=True,
)
def test_has_sent_sep_false(sent_sep_false_pairs):
  for text, expected in sent_sep_false_pairs:
    assert has_sent_sep(text) == expected


@pytest.fixture
def sep_true_pairs(request):
  return [
    (f'{request.param}', [f'{request.param}']),
    (f'{request.param}a', [f'{request.param}', 'a']),
    (f'a{request.param}', ['a', f'{request.param}']),
    (f'a{request.param}b', [f'a{request.param}b']),
  ]


@pytest.mark.parametrize(
  'sep_true_pairs',
  ['。', '！', '？', '\\n', '\\N'],
  indirect=True,
)
def test_split_sent_sep_true(sep_true_pairs):
  for text, expected in sep_true_pairs:
    assert split_sent_sep(text) == expected


@pytest.fixture
def sep_false_pairs(request):
  return [
    (f'{request.param}', [f'{request.param}']),
    (f'{request.param}a', [f'{request.param}a']),
    (f'a{request.param}', [f'a{request.param}']),
    (f'a{request.param}b', [f'a{request.param}b']),
  ]


@pytest.mark.parametrize(
  'sep_false_pairs',
  '､、：；，…',
  indirect=True,
)
def test_split_sent_sep_false(sep_false_pairs):
  for text, expected in sep_false_pairs:
    assert split_sent_sep(text) == expected
