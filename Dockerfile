# Must build from lume-services repository root due to file paths
FROM condaforge/miniforge3:latest AS build

COPY lume_services/docker/files/environment.yml /lume/environment.yml
COPY . /lume/lume-services

RUN conda install -c conda-forge conda-pack && \
    conda env create --file /lume/environment.yml && \
    conda run -n lume-services pip install /lume/lume-services

# Use conda-pack to create a  enviornment in /venv:
RUN conda-pack -n lume-services -o /tmp/env.tar && \
  mkdir /venv && cd /venv && tar xf /tmp/env.tar && \
  rm /tmp/env.tar

# No longer need conda, just the packed python
FROM debian:buster AS runtime

ENV EXTRA_CONDA_PACKAGES=""
ENV EXTRA_PIP_PACKAGES=""

ARG LUME_SERVICES_VERSION
ENV LUME_SERVICES_VERSION=$LUME_SERVICES_VERSION

ENV PATH="${PATH}:/venv/bin"

# Copy /venv from the previous stage:
COPY --from=build /venv /venv

# requires bash
SHELL ["/bin/bash", "-c"]
# Fix paths, will be same in final image so this is fine
RUN source /venv/bin/activate && \
    /venv/bin/conda-unpack

# must set bash shell to use source below
COPY lume_services/docker/files/entrypoint.sh /prefect/entrypoint.sh
RUN chmod +x /prefect/entrypoint.sh

SHELL ["/prefect/entrypoint.sh", "/bin/bash", "-c"]
ENTRYPOINT [ "/prefect/entrypoint.sh" ]


# Production build using released lume-services version
#FROM builder AS prod

#ARG LUME_SERVICES_VERSION
#ENV LUME_SERVICES_VERSION=$LUME_SERVICES_VERSION

#ARG LUME_SERVICES_REPOSITORY
#ENV LUME_SERVICES_REPOSITORY=$LUME_SERVICES_REPOSITORY

#RUN pip install ${LUME_SERVICES_REPOSITORY}/archive/refs/tags/${LUME_SERVICES_VERSION}
