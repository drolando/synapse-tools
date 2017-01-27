FROM docker-dev.yelpcorp.com/lucid_yelp
MAINTAINER John Billings <billings@yelp.com>

RUN apt-get update

RUN apt-get -y install \
    dpkg-dev \
    python-tox \
    python-setuptools \
    python2.7 \
    python2.7-dev \
    python-pkg-resources \
    debhelper \
    libyaml-dev \
    libcurl4-openssl-dev \
    libffi-dev \
    libssl-dev \
    build-essential \
    dh-virtualenv

RUN pip install -U pip
RUN /usr/bin/update-alternatives --install /usr/bin/pip pip /usr/local/bin/pip 3
RUN pip install -U tox

WORKDIR /work
