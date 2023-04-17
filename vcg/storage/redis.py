# Path: vcg/storage/redis.py

import os

import redis

from utils.decorator import check_env


@check_env('REDIS_HOST', 'REDIS_PORT', 'REDIS_PASS', 'REDIS_USER')
def create_client():
  return redis.StrictRedis(
    host=os.getenv('REDIS_HOST'),
    port=os.getenv('REDIS_PORT'),
    username=os.getenv('REDIS_USER'),
    password=os.getenv('REDIS_PASS'),
  )
