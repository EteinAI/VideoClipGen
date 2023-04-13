
import re


left_punct = r'[“‘（［｛〔《「『【〖〘〚〝﹙﹛﹝]'
sent_sep = [r'。', r'！', r'？', r'\\n', r'\\N']
chs_punct_pattern = '[\u3000-\u303f\uFF00-\uFFEF]'
eng_punct_pattern = '[\u0021-\u002f\u003a-\u0040\u005b-\u0060\u007b-\u007e]'
chs_punct = '！？｡。＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝〜～｟｠\｢｣､、〃《》「」『』【】〔〕〖〗〘〙〚〛〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏.'


def has_left_punct(str):
  pattern = r'^\s*' + left_punct + r'.*'
  return re.match(pattern, str) is not None


def has_sent_sep(str):
  pattern = \
    r'.*[' + '|'.join(sent_sep) + r']\s*$' + r'|' + \
    r'^\s*[' + '|'.join(sent_sep) + r'].*'
  return re.match(pattern, str) is not None


# HACK! split by sent_sep if it locates at the begin/end of the string, ignore
# middle ones
def split_sent_sep(str):
  pattern = \
    r'(' + '|'.join(sent_sep) + r')\s*$' + r'|' + \
    r'^\s*(' + '|'.join(sent_sep) + r')'
  return [x for x in re.split(pattern, str) if x]


# from https://github.com/hankcs/HanLP/blob/master/hanlp/utils/rules.py
def replace_sent_sep(text):
  hard_sep = [
    r'([｡。！？\?](?=$|[^”’]))',
    r'(\.{3,6}(?=[^”’]))',
    r'(…{1,2}(?=[^”’]))',
    r'([｡。！？\?][”’](?=[^，。！？?]))',
  ]

  soft_sep = [
    r'([,，；](?=$|[^”’]))',
  ]

  text = re.sub('|'.join(hard_sep), r'\\N', text)
  text = re.sub('|'.join(soft_sep), r'\\n', text)

  return text


def remove_punct(text):
  '''
  Remove Chinese and English punctuation from text, as well as all spaces.
  '''
  return re.sub(r'[^\w]', '', text)
