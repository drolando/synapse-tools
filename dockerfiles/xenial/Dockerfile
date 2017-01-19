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
    dh-virtualenv \
    protobuf-compiler

WORKDIR /work
