#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
.venv/bin/python orbisacta.py run >> data/scheduler.log 2>&1
