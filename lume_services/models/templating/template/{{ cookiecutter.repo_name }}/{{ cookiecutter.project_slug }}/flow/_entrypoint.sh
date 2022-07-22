#!/usr/bin/env bash

set -ef -o pipefail

source /venv/bin/activate

exec "$@"
