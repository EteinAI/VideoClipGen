# VideoClipGen

[![Test CI](https://github.com/EteinAI/VideoClipGen/actions/workflows/pytest.yml/badge.svg)](https://github.com/EteinAI/VideoClipGen/actions/workflows/pytest.yml)
[![Coverage](https://img.shields.io/endpoint?url=https://gist.github.com/EteinAI/d2252855dcf797fe1d205982bef0c9be/raw/vcg_heads_main.json)](https://github.com/EteinAI/VideoClipGen/actions/workflows/pytest.yml)

> Autonomous video clip generation

Imagine being able to turn your favorite Weixin article into a stunning video clip with just a few clicks. Our project does just that, automatically generating captivating 30 to 60-second videos that bring your Weixin content to life in a whole new way. With our cutting-edge technology, you can showcase your articles in a visually stunning format that will capture your audience's attention like never before. So why settle for static text when you can make your content pop with our innovative video generation solution? Try it out today and experience the power of dynamic visual storytelling!

# Development

## MacOS

**Create new python virtual env with conda**

```bash
# use miniforge to manage conda env
brew install miniforge

# create virtual env
# naming the env as vcg, or whatever you like
conda create --name vcg python=3.11
conda activate vcg
```

**_Strongly recommended to perform the following steps in a virtual env for optimal isolation and to prevent any interference with your base environment._**

> More about conda virtual env management
>
> ```bash
> # list all virtual envs
> conda env list
> # deactivate current virtual env
> conda deactivate
> # remove virtual env
> conda env remove -n {env_name}
> # reset virtual env
> conda install --rev {REV_NUM}
> ```

**Install FFmpeg**

`FFmpeg` is required to generate video clips.

```bash
# install ffmpeg with homebrew
brew install ffmpeg
```

**Code and dependencies**

```bash
git clone git@github.com:EteinAI/VideoClipGen.git

# install pytorch with MPS (Metal Performance Shaders) backend
# https://developer.apple.com/metal/pytorch/
conda install pytorch torchvision torchaudio -c pytorch-nightly

# verify mps status
# you should see "device='mps:0'"
cd VideoClipGen
python -m scripts.mps_check
```

**Install dependencies**

```bash
# In the root directory
pip install -r requirements.txt

# preload models
python -m scripts.load_models
```

### API Keys

API keys are required to invoke third-party services, including:

**TTS (Aliyun)**

- Create a `.env` file in `/path/to/code/vcg/speechsynthesis` folder
- Add **`ALI_ACCESSKEY_ID`**, **`ALI_ACCESSKEY_SECRET`** and **`ALI_APP_KEY`** into `.env` file

**Text summary (ChatGPT)**

- Create a `.env `file in `/path/to/code/vcg/textsummary` folder
- Add **`PROXY_API_KEY`** into `.env` file

> VideoClipGen use load-dotenv to load environment variables from .env file, but as long as these IDs and KEYs can be found in the environment variables, it should work.

### Verify local environment

Invoke tests to verify the integrity of local environment

```bash
# make sure .env files are created and filled with correct keys
cd /path/to/code/
pytest
```

### Run workflow locally

```bash
# make sure .env files are created and filled with correct keys
cd /path/to/code/
python vcg/localflow.py --params params.json
```

## Testing

VideoClipGen uses pytest to run tests.

```bash
# run all tests
pytest
# run tests in a more verbose mode
# -s means show all outputs, -v stands for verbose
pytest -s -v

# run tests in a specific file
pytest tests/test_tts.py
# run tests in a specific function
pytest tests/test_tts.py::test_tts
```

## Workflow

VideoClipGen uses [temporalio](https://github.com/temporal/temporal) as the workflow engine, and use temporalite to do local development.

Regarding local development, [temporalite](https://github.com/temporal/temporalite) is preferred over temporal server since it is much easier to setup and use.

For more temporalio related information, please refer to [Temporal's documentation](https://docs.temporal.io/docs/)

### Temporal Lite

First, download and extract the latest release from [GitHub](https://github.com/temporalio/temporalite/releases/latest).

To start Temporal server:

```bash
# start a in-memory temporal service with namespace `default`
temporalite start --ephemeral -n default

# start temporal service that persist workflow records in vcg_dev.db (sqlite)
temporalite start -f vcg_dev.db -n default
```

At this point you should have a server running on localhost:7233 and a web interface at http://localhost:8233.

Use [Temporal's command line tool](https://docs.temporal.io/tctl) `tctl` to interact with the local Temporalite server.

```bash
# install tctl with homebrew
brew install tctl

# run a workflow
# namespace: default, task queue: default, timeout: 2400
# workflow type: VideoClipGen, parameters: params.json, workflow id: anything
tctl --ns default workflow run \
  --tq default --et 2400 \
  --wt VideoClipGen --if params.json --wid 100
```

### Workflow parameters

`param.json` contains workflow parameters, including:

- **cwd**: working directory where to put generated contents when executing workflow locally
- **url**: weixin article url
- output(optional): overwrite the default filename(`output.mp4`) of the generated video clip which can be found in `cwd`
- voice_ali(optional): specify the voice to synthesize speech when using aliyun, candidates can be found [here](https://help.aliyun.com/document_detail/84435.html)

> Default param file can be found at /path/to/code/params.json

### Run workflow

```bash
# first start temporal server (assuming in memory mode)
temporalite start --ephemeral -n default

# then start workflow
# --server and --task-queue are optional
python vcg/temoralflow.py --server localhost:7233 --task-queue default

# run a workflow with tctl
# namespace: default, task queue: default, timeout: 2400
# workflow type: VideoClipGen, parameters: params.json, workflow id: anything
tctl --ns default workflow run \
 --tq default --et 2400 \
 --wt VideoClipGen --if params.json --wid 100
```
