
import argparse
import ffmpeg
import json
import os

from pathlib import Path
from hashlib import sha1
from bs4 import BeautifulSoup
import urllib.request as request
from pprint import pprint


# 将图片保存到本地
def download_img(url: str, path: str) -> str:
  if not os.path.exists(path):
    os.makedirs(path)
  s1 = sha1()
  s1.update(url.encode("utf-8"))
  local_path = os.path.join(path, s1.hexdigest() + '.jpg')
  return request.urlretrieve(url, local_path)[0]


def build_soup(url: str) -> BeautifulSoup:
  resource = request.urlopen(url)
  html = resource.read().decode(resource.headers.get_content_charset())
  soup = BeautifulSoup(html, 'lxml')
  return soup


def get_metadata(soup: BeautifulSoup) -> dict[str, str]:
  # share_title = soup.find_all(property='og:title') #分享标题,返回的列表，实际中只有一条，用find()更合适
  share_title = soup.find(property='og:title')  # 分享标题行
  share_title_con = share_title.get('content')  # 分享标题文本
  print("title:", share_title_con)

  share_url = soup.find(property='og:url')  # 分享url行
  share_url_con = share_url.get('content')  # 分享url地址文本
  print("share url:", share_url_con)

  share_desc = soup.find(property='og:description')  # 分享描述行
  share_desc_con = share_desc.get('content')  # 分享描述文本
  print("share desc:", share_desc_con)

  share_img = soup.find(property='og:image')  # 分享头图行
  share_img_con = share_img.get('content')  # 分享头图地址，微信有防盗链机制，所以图片需要下载到本地
  print("share image:", share_img_con)

  return {
    'title': str(share_title_con),
    'url': str(share_url_con),
    'desc': str(share_desc_con),
    'image': str(share_img_con)
  }


def get_paragraphs(body) -> list[str]:
  # 文章正文内容
  main = body.find(id="js_content")

  # split but keep the delimiter
  separator = '。'
  paragraphs = [s + separator for s in main.get_text(strip=True).split('。')]
  pprint(paragraphs)

  return paragraphs


def get_images(body, path: str) -> list[str]:
  image_paths = []

  # 文章中的所有图片
  images = body.find_all('img')
  for image in images:
    src = image.get('data-src')
    if src:
      new_src = download_img(src, path)
      print(new_src)
      image_paths.append(new_src)
      # 前端图片展示时需要用延迟加载
      image['data-src'] = new_src

  return image_paths


def split_frames(images, outdir):
  if not os.path.exists(outdir):
    os.makedirs(outdir)

  for i, image in enumerate(images):
    stream = ffmpeg.input(image)
    stream = ffmpeg.output(
      stream,
      os.path.join(outdir, f'{i}-%d.jpg'),
      # avoid dropping frames
      # fps_mode='passthrough',
      vsync=0,
      pix_fmt='yuvj420p',
      # 10 frames maximum
      vframes=10,
    )
    ffmpeg.run(stream, quiet=True)

  return [str(p) for p in Path(outdir).glob('**/*.jpg')]


def parse(url: str, path: str) -> tuple[list[str], list[str], dict[str, str]]:
  soup = build_soup(url)
  body = soup.find(id='activity-detail')

  metadata = get_metadata(soup)
  sentences = get_paragraphs(body)
  images = get_images(body, os.path.join(path, 'tmpimages'))

  with open(os.path.join(path, 'sentences.json'), 'w') as fp:
    json.dump(sentences, fp, ensure_ascii=False, indent=2)
    fp.close()
  with open(os.path.join(path, 'metadata.json'), 'w') as fp:
    json.dump(metadata, fp, ensure_ascii=False, indent=2)
    fp.close()

  return sentences, split_frames(images, os.path.join(path, 'images')), metadata
