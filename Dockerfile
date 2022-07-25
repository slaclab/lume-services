# Must build from lume-services repository root due to file paths
FROM condaforge/miniforge3:latest

ENV EXTRA_CONDA_PACKAGES=""
ENV EXTRA_PIP_PACKAGES=""

ARG LUME_SERVICES_VERSION
ENV LUME_SERVICES_VERSION=$LUME_SERVICES_VERSION

COPY entrypoint.sh /prefect/entrypoint.sh
COPY environment.yml /lume/environment.yml
COPY . /lume/lume-services

RUN conda env update --name base --file /lume/environment.yml && \
    conda run -n base pip install /lume/lume-services && \
    chmod +x /prefect/entrypoint.sh

ENTRYPOINT [ "/prefect/entrypoint.sh" ]


# Production build using released lume-services version
#FROM builder AS prod

#ARG LUME_SERVICES_VERSION
#ENV LUME_SERVICES_VERSION=$LUME_SERVICES_VERSION

#ARG LUME_SERVICES_REPOSITORY
#ENV LUME_SERVICES_REPOSITORY=$LUME_SERVICES_REPOSITORY

#RUN pip install ${LUME_SERVICES_REPOSITORY}/archive/refs/tags/${LUME_SERVICES_VERSION}
