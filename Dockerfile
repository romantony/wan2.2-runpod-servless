FROM nvidia/cuda:12.8.0-cudnn-runtime-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    WAN_HOME=/workspace/Wan2.2 \
    WAN_CKPT_DIR=/workspace/models

RUN apt-get update && apt-get install -y --no-install-recommends \
    git git-lfs python3 python3-pip python3-venv curl wget ca-certificates tini ffmpeg \
 && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip && \
    pip install --index-url https://download.pytorch.org/whl/cu128 \
        torch torchvision torchaudio

WORKDIR /workspace
RUN git clone https://github.com/Wan-Video/Wan2.2.git && cd Wan2.2 && pip install -r requirements.txt || true

COPY requirements.txt /workspace/requirements.txt
RUN pip install -r /workspace/requirements.txt

COPY src /workspace/src
COPY scripts /workspace/scripts
RUN chmod +x /workspace/scripts/bootstrap.sh

ENV RUNPOD_MAX_CONCURRENCY=1

ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["/bin/bash","/workspace/scripts/bootstrap.sh"]
