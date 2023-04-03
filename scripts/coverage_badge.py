
import coverage
import json


COLOR_RANGES = [
  (95, 'brightgreen'),
  (90, 'green'),
  (75, 'yellowgreen'),
  (60, 'yellow'),
  (40, 'orange'),
  (0, 'red'),
]


def get_total():
  """
  Return the rounded total as properly rounded string.
  """

  class Devnull(object):
    """
    A file like object that does nothing.
    """

    def write(self, *args, **kwargs):
      pass

  cov = coverage.Coverage()
  cov.load()
  return cov.report(file=Devnull())


def get_color(total):
  """
  Return color for current coverage precent
  """
  try:
    xtotal = int(total)
  except ValueError:
    return 'lightgrey'
  for range_, color in COLOR_RANGES:
    if xtotal >= range_:
      return color


if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('--file-path', required=True, type=str)

  total = get_total()
  info = {
    'schemaVersion': 1,
    'label': 'Coverage',
    'namedLogo': 'pytest',
    'color': get_color(total),
    'message': f'{round(total)}%',
  }

  with open(parser.parse_args().file_path, 'w') as fp:
    json.dump(info, fp, ensure_ascii=False, indent=2)
