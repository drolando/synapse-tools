FROM ubuntu:xenial
MAINTAINER John Billings <billings@yelp.com>

RUN apt-get update && apt-get -y install \
    debhelper \
    dpkg-dev \
    libyaml-dev \
    libcurl4-openssl-dev \
    python-dev \
    python-tox \
    python-setuptools \
    libffi-dev \
    libssl-dev \
    build-essential \
    protobuf-compiler \
    gdebi-core \
    wget

RUN cd /tmp && \
    wget http://mirrors.kernel.org/ubuntu/pool/universe/d/dh-virtualenv/dh-virtualenv_1.0-1_all.deb && \
    gdebi -n dh-virtualenv*.deb && \
    rm dh-virtualenv_*.deb

WORKDIR /work
