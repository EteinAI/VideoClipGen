from vcg.imageretrieval.retrieval import TextEmbeddings, ImageEmbeddings

if __name__ == '__main__':
  # create new object of each class to preload the models
  # kind of HACK but works for now
  print(f'Image embedding model: {ImageEmbeddings.instance().name}')
  print(f'Text embedding model: {TextEmbeddings.instance().name}')
