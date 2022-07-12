# Must build from lume-services repository root due to file paths
FROM condaforge/miniforge3:latest as builder

ARG PREFECT_VERSION
ENV PREFECT_VERSION=$PREFECT_VERSION

ENV EXTRA_CONDA_PACKAGES=""
ENV EXTRA_PIP_PACKAGES=""

COPY entrypoint.sh /prefect/entrypoint.sh

RUN conda install python=3.9 prefect=$PREFECT_VERSION && \
    chmod +x /prefect/entrypoint.sh

ENTRYPOINT [ "/prefect/entrypoint.sh" ]

FROM builder AS dev

ARG LUME_SERVICES_REPOSITORY
ENV LUME_SERVICES_REPOSITORY=$LUME_SERVICES_REPOSITORY

ARG LUME_SERVICES_VERSION
ENV LUME_SERVICES_VERSION=$LUME_SERVICES_VERSION

COPY requirements.txt /tmp/requirements.txt
COPY . /tmp/lume-services

RUN conda install --file /tmp/requirements.txt && \
    pip install /tmp/lume-services && \
    rm -rf /tmp/lume-services

# Production build using released lume-services version
FROM builder AS prod

ARG LUME_SERVICES_REPOSITORY
ENV LUME_SERVICES_REPOSITORY=$LUME_SERVICES_REPOSITORY

ARG LUME_SERVICES_VERSION
ENV LUME_SERVICES_VERSION=$LUME_SERVICES_VERSION

RUN pip install ${LUME_SERVICES_REPOSITORY}/archive/refs/tags/${LUME_SERVICES_VERSION}
