#!/bin/bash
set -x

pwd

ls -la


uv run ./src/mindloom/main.py --host 0.0.0.0 --port 8000
