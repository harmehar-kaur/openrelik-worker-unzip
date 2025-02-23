# Use the official Docker Hub Ubuntu base image
FROM ubuntu:24.04

# Prevent needing to configure debian packages, stopping the setup of
# the docker container.
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

# Install poetry and any other dependency that your worker needs.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-poetry \
    wget \
    unzip \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Download and extract 7-Zip, then move it to /forensics/
RUN wget https://www.7-zip.org/a/7z2409-linux-x64.tar.xz && \
    mkdir -p /forensics/7zip && \
    tar -xf 7z2409-linux-x64.tar.xz -C /forensics/7zip && \
    chmod +x /forensics/7zip/7zz && \
    rm 7z2409-linux-x64.tar.xz
    
# Configure poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Configure debugging
ARG OPENRELIK_PYDEBUG
ENV OPENRELIK_PYDEBUG ${OPENRELIK_PYDEBUG:-0}
ARG OPENRELIK_PYDEBUG_PORT
ENV OPENRELIK_PYDEBUG_PORT ${OPENRELIK_PYDEBUG_PORT:-5678}

# Set working directory
WORKDIR /openrelik

# Copy poetry toml and install dependencies
COPY ./pyproject.toml ./poetry.lock .
RUN poetry install --no-interaction --no-ansi

# Copy files needed to build
COPY . ./

# Install the worker and set environment to use the correct python interpreter.
RUN poetry install && rm -rf $POETRY_CACHE_DIR
ENV VIRTUAL_ENV=/app/.venv PATH="/openrelik/.venv/bin:$PATH"

# Default command if not run from docker-compose (and command being overidden)
CMD ["celery", "--app=src.tasks", "worker", "--task-events", "--concurrency=1", "--loglevel=INFO"]
