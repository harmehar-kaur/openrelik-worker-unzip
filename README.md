# OpenRelik Worker Unzip

## Overview
The **OpenRelik Worker Unzip** is a task worker for **OpenRelik** that extracts files from ZIP archives. It integrates with the OpenRelik ecosystem, processing uploaded ZIP files and extracting their contents automatically.

## Features
- Uses `unzip` to extract archive contents.
- Runs as a Celery worker, listening on the `openrelik-worker-unzip` queue.
- Supports automatic task execution within OpenRelik workflows.

## Installation
To deploy this worker, ensure it's included in your `docker-compose.yml` file:

```yaml
  openrelik-worker-unzip:
    container_name: openrelik-worker-unzip
    image: ghcr.io/openrelik/openrelik-worker-unzip:${OPENRELIK_WORKER_UNZIP_VERSION}
    restart: always
    environment:
      - REDIS_URL=redis://openrelik-redis:6379
      - OPENRELIK_PYDEBUG=0
    volumes:
      - ./data:/usr/share/openrelik/data
    command: "celery --app=src.app worker --task-events --concurrency=2 --loglevel=INFO -Q openrelik-worker-unzip"
```

## Usage
This worker listens for tasks in the OpenRelik task queue. When a ZIP file is uploaded, it extracts the contents to the specified output directory.

## Environment Variables
- `REDIS_URL`: Redis connection string for task management.
- `OPENRELIK_PYDEBUG`: Set to `1` to enable debugging, `0` to disable.
