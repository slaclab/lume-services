#!/bin/bash
set -e

prefect backend server

if [ -n "$EXTRA_CONDA_PACKAGES" ] && [ "$LOCAL_CHANNEL_ONLY" = "true" ]; then

  if [ ! -d "$LOCAL_CONDA_CHANNEL" ]; then
    echo "Must mount conda channel to $LOCAL_CONDA_CHANNEL"
    exit 1
    fi

  echo "+conda install --yes -c file://$LOCAL_CONDA_CHANNEL $EXTRA_CONDA_PACKAGES --offline"
  conda install --yes -c "file://$LOCAL_CONDA_CHANNEL" $EXTRA_CONDA_PACKAGES --offline
else
  if [ -n "$EXTRA_CONDA_PACKAGES" ]; then
    echo "+conda install --yes $EXTRA_CONDA_PACKAGES"
    conda install --yes $EXTRA_CONDA_PACKAGES
  fi

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
