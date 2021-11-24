# syntax=docker/dockerfile:1
FROM ubuntu:20.04
WORKDIR /coality
ENV DEBIAN_FRONTEND noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN true
COPY . .
RUN apt-get update && apt-get install -y \
dos2unix \
wget \
python3 \
python3-pip \
git \
libxml2 \
libcurl4 \
libarchive13
RUN find . -type f -print0 | xargs -0 dos2unix
RUN ./setup.sh
ENV PYTHONPATH="${PYTHONPATH}:/$PROJECT_PATH"