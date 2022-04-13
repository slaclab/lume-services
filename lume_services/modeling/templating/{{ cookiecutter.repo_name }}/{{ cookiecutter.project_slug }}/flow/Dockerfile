FROM continuumio/miniconda3 AS build

# Create environment
COPY ./environment.yml .


ARG VERSION
ENV version=$VERSION

RUN conda env create -f ./environment.yml && \
    conda run -n {{ cookiecutter.project_slug }} python -m pip install {{ cookiecutter.github_url }}/archive/refs/tags/$version.tar.gz

# Install conda-pack:
RUN conda install -c conda-forge conda-pack

# Use conda-pack to create a  enviornment in /venv:
RUN conda-pack -n {{ cookiecutter.project_slug }} -o /tmp/env.tar && \
  mkdir /venv && cd /venv && tar xf /tmp/env.tar && \
  rm /tmp/env.tar

# Fix paths, will be same in final image so this is fine
RUN /venv/bin/conda-unpack

# No longer need conda, just the packed python
FROM debian:buster AS runtime

# Copy /venv from the previous stage:
COPY --from=build /venv /venv

COPY _entrypoint.sh /usr/local/bin/_entrypoint.sh
RUN chmod +x /usr/local/bin/_entrypoint.sh

RUN mkdir /opt/prefect
COPY flow.py /opt/prefect/flow.py

# When image is run, run the code with the environment
# activated:
SHELL ["/usr/local/bin/_entrypoint.sh", "/bin/bash", "-c"]

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh"]