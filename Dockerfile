FROM ubuntu:22.04

# This is from https://hub.docker.com/r/yahwang/ubuntu-pyenv/dockerfile
ARG PYTHON_VERSION=3.11
ARG BUILD_PYTHON_DEPS=" \
        make \
        build-essential \
        libbz2-dev \
        libffi-dev \
        libgdbm-dev \
        liblzma-dev \
        libncurses5-dev \
        libncursesw5-dev \
        libnss3-dev \
        libreadline-dev \
        libsqlite3-dev \
        libssl-dev \
        xz-utils \
        zlib1g-dev \
        "
ARG BUILD_OPT_DEPS=" \
        sudo \
        locales \
        git \
        ca-certificates \
        curl \
        jq \
        zip \
        "

# basic update & locale setting
RUN apt-get update \
 && apt-get upgrade -yqq \
 && apt-get install -yqq --no-install-recommends \
        ${BUILD_PYTHON_DEPS} \
        ${BUILD_OPT_DEPS} \
 && localedef -f UTF-8 -i en_US en_US.UTF-8 \
 && useradd -m -s /bin/bash ubuntu \
 && echo 'ubuntu ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers \
 && apt-get autoremove -yqq --purge \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

USER ubuntu

WORKDIR /home/ubuntu

ENV LANG=en_US.UTF-8 \
    PYENV_ROOT="/home/ubuntu/.pyenv" \
    PATH="/home/ubuntu/.pyenv/versions/${PYTHON_VERSION}/bin:/home/ubuntu/.pyenv/bin:/home/ubuntu/.pyenv/shims:$PATH"

# install tippecanoe
ARG TIPPECANOE_VERSION=2.29.0
RUN curl -sL https://github.com/felt/tippecanoe/archive/refs/tags/${TIPPECANOE_VERSION}.tar.gz | tar -xz \
 && cd tippecanoe-${TIPPECANOE_VERSION} \
 && make -j \
 && sudo make install \
 && cd .. \
 && rm -rf tippecanoe-${TIPPECANOE_VERSION}

# install pyenv & python
RUN curl https://pyenv.run | bash \
 && pyenv install ${PYTHON_VERSION} \
 && pyenv global ${PYTHON_VERSION} \
 && pip install --upgrade pip pipenv==2023.12.1

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
RUN pipenv install --dev --deploy --system && pyenv rehash

RUN playwright install-deps
RUN playwright install firefox

COPY . .

ARG GIT_COMMIT
ENV GIT_COMMIT=$GIT_COMMIT

CMD ["/home/ubuntu/ci/run_all_spiders.sh"]
