FROM openjdk:15-jdk-alpine3.12 AS base

ARG PYTHON_VERSION='3.8.12'

RUN apk --update upgrade
RUN apk add --no-cache \
  bash \
  build-base \
  bzip2-dev \
  ca-certificates \
  curl `# Needed by pyenv and for monitoring` \
  git `# Needed by pyenv` \
  libffi-dev \
  libxslt-dev \
  linux-headers \
  ncurses-dev \
  openssl-dev \
  readline-dev \
  sqlite-dev 

ENV HOME /app
ENV PYENV_ROOT $HOME/.pyenv
ENV PYTHON_VERSION $PYTHON_VERSION
ENV PATH $PYENV_ROOT/shims:$PATH:$PYENV_ROOT/bin

ENV CRYPTOGRAPHY_DONT_BUILD_RUST 1

RUN curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer \
  -o pyenv-installer && \
  /bin/bash pyenv-installer && \
  rm pyenv-installer
  
RUN pyenv install $PYTHON_VERSION
RUN pyenv global $PYTHON_VERSION
RUN pyenv rehash

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./tjrj.py" ]