import faiss
import numpy as np
import torch

import clip
from PIL import Image

from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

from multilingual_clip import pt_multilingual_clip as lang
import transformers

device = 'cuda' if torch.cuda.is_available() else 'cpu'


class TextEmbeddings:
  _model_name = 'M-CLIP/XLM-Roberta-Large-Vit-L-14'
  _singleton = None

  @classmethod
  def instance(cls):
    if TextEmbeddings._singleton is None:
      TextEmbeddings._singleton = TextEmbeddings()
    return TextEmbeddings._singleton

  def __init__(self) -> None:
    self._model = lang.MultilingualCLIP.from_pretrained(self.name)
    self._tokenizer = transformers.AutoTokenizer.from_pretrained(self.name)

  def encode(self, sentences: list[str]):
    """Get text embeddings for a list of sentences."""
    with torch.no_grad():
      embeddings = self._model.forward(sentences, self._tokenizer)
      embeddings /= embeddings.norm(dim=-1, keepdim=True)
      return embeddings.detach().cpu().numpy()

  @property
  def name(self):
    return TextEmbeddings._model_name


class ImageEmbeddings:
  _model_name = 'ViT-L/14'
  _singleton = None

  @classmethod
  def instance(cls):
    if ImageEmbeddings._singleton is None:
      ImageEmbeddings._singleton = ImageEmbeddings()
    return ImageEmbeddings._singleton

  def __init__(self) -> None:
    super().__init__()
    self._model, self._preprocess = clip.load(self.name, device=device)

  def encode(self, image_files: list[str]):
    """Get image embeddings for a list of image files."""
    image_tensors = [self._preprocess(Image.open(f)).unsqueeze(0).to(device)
                     for f in image_files]
    with torch.no_grad():
      embeddings = np.vstack([self._model.encode_image(tensor).cpu().numpy()
                              for tensor in image_tensors])
      return embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

  @property
  def name(self):
    return ImageEmbeddings._model_name


def clustering(embeddings, k=2) -> list[list[int]]:
  # Calculate cosine similarity between embeddings
  similarity_matrix = cosine_similarity(embeddings)

  # Perform K-Means clustering on the similarity matrix
  kmeans = KMeans(
    n_clusters=k,
    random_state=0,
    n_init=10
  ).fit(similarity_matrix)

  # Group the images based on their cluster assignments
  groups: list[list[int]] = [[] for _ in range(k)]
  for i, idx in enumerate(kmeans.labels_):
    groups[idx].append(i)

  return sorted(groups, key=lambda x: len(x), reverse=True)


def retrieve(sentences, images):
  """Retrieve images for a list of sentences."""

  # HACK! hardcoded preprocessing
  # Drop images whose width/height ratio larger that 2
  s = [Image.open(f).size for f in images]
  images = sorted([images[i]
                   for i in range(len(images)) if s[i][0] / s[i][1] < 2])

  image_embeddings = ImageEmbeddings.instance().encode(images)
  text_embeddings = TextEmbeddings.instance().encode(sentences)

  # HACK! assume the majority group is the one contains the query image
  groups = clustering(image_embeddings, k=2)
  print(f'Clusters: {groups}')

  # HACK! if merge two groups if not enough images in the majority group
  if len(groups[0]) < len(sentences):
    groups = [groups[0] + groups[1], []]

  kept = [images[i] for i in groups[0]]
  dropped = [images[i] for i in groups[1]]
  image_embeddings = image_embeddings[groups[0]]

  scores = np.dot(text_embeddings, image_embeddings.T)
  indices = np.argsort(scores, axis=1)[:, ::-1]
  print(f'Scores: {scores}')
  print(f'Indices: {indices}')

  seen = []
  selected = []
  for items in indices:
    selected.append([])
    for i in items:
      if kept[i] not in seen:
        seen.append(kept[i])
        selected[-1].append(kept[i])
        # For now, only select one image for each sentence
        break

  return selected, kept, dropped
