import sys

from vcg.imageretrieval.retrieval import TextEmbeddings, ImageEmbeddings

if __name__ == '__main__':
  # create new object of each class to preload the models
  # kind of HACK but works for now
  TextEmbeddings()
  print('Text model loaded')
  ImageEmbeddings()
  print('Image model loaded')
  sys.exit(0)
