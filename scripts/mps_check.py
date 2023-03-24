# Description: Check if MPS (Metal Performance Shaders) backend is available

import torch

if __name__ == '__main__':
  if torch.backends.mps.is_available():
    mps_device = torch.device("mps")
    x = torch.ones(1, device=mps_device)
    print(x)
  else:
    print("MPS device not found.")
