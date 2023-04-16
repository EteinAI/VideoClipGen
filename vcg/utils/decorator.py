
import os

from functools import wraps


# decorator to verify environment variables
def check_env(*keys):
  for key in keys:
    if os.getenv(key) is None:
      raise RuntimeError(f'{key} not found in env or in .env file')

  def inner(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
      return func(*args, **kwargs)
    return wrapper
  return inner
