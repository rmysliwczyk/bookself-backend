#!/bin/bash
set -e

#alembic upgrade head - For later
fastapi run --host 0.0.0.0 --port 8404
