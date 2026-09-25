FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    postgresql \
    postgresql-contrib \
    redis-server \
    sudo \
  && rm -rf /var/lib/apt/lists/*

# Astral uv (Python toolchain used by the backend Makefile targets).
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Match the default Cloud Agent runtime user when present.
RUN if id ubuntu >/dev/null 2>&1; then \
      mkdir -p /home/ubuntu/.local/bin \
      && cp -a /root/.local/bin/uv /home/ubuntu/.local/bin/ \
      && chown -R ubuntu:ubuntu /home/ubuntu/.local; \
    fi

USER ubuntu
