#!/bin/bash
set -e

source /venv/bin/activate
prefect backend server

if [ -n "$EXTRA_CONDA_PACKAGES" ]; then
  echo "+conda install --yes $EXTRA_CONDA_PACKAGES"
  conda install --yes $EXTRA_CONDA_PACKAGES
fi

# need to handle pip offline...
if [ ! -z "$EXTRA_PIP_PACKAGES" ]; then
  echo "+pip install $EXTRA_PIP_PACKAGES"
  pip install $EXTRA_PIP_PACKAGES
fi

if [ -z "$*" ]; then
  echo "\
            _____  _____  ______ ______ ______ _____ _______
           |  __ \|  __ \|  ____|  ____|  ____/ ____|__   __|
           | |__) | |__) | |__  | |__  | |__ | |       | |
           |  ___/|  _  /|  __| |  __| |  __|| |       | |
           | |    | | \ \| |____| |    | |___| |____   | |
           |_|    |_|  \_\______|_|    |______\_____|  |_|
This is the Prefect image for use with lume-services version ${LUME_SERVICES_VERSION}
"
  exec bash --login
else
  exec "$@"
fi
