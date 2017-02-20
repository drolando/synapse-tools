FROM docker-dev.yelpcorp.com/lucid_yelp
MAINTAINER John Billings <billings@yelp.com>

RUN apt-get update

RUN apt-get -y install \
    dpkg-dev \
    python-tox \
    python-setuptools \
    python2.7 \
    python2.7-dev \
    debhelper \
    libyaml-dev \
    libcurl4-openssl-dev \
    libffi-dev \
    libssl-dev \
    build-essential \
    dh-virtualenv

WORKDIR /work
