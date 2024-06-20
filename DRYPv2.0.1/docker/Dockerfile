# get the python image
FROM python:3.11-slim

# set env
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DOCKER_CONTAINER Yes

ARG instance_type

# Default values provided to cover Windows users but as Windows doesn't mount locations in the
# same way as Linux and MacOS
ARG USER_ID=10001
ARG GROUP_ID=10001

RUN apt-get update
RUN apt-get -y install build-essential
RUN apt-get -y install gcc
# Install some utilities
RUN apt-get -y install wget
RUN apt-get -y install nano
RUN apt-get -y install unzip
#RUN apt-get -y install curl
RUN apt-get -y install gfortran

RUN mkdir -p /srv/projects/dryp

WORKDIR /srv/projects/dryp
COPY . /srv/projects/dryp
RUN pip install --upgrade pip~=23.3.1
RUN find /usr/local/lib/python*/site-packages/ -name '*.exe' -exec rm -f {} \;

RUN groupadd -f -g ${GROUP_ID} dryp
# do not log creating new user, otherwise there could be a lot of messages
RUN useradd -r --no-log-init -u ${USER_ID} -g dryp dryp
RUN install -d -m 0755 -o dryp -g dryp /home/dryp

RUN apt-get -y autoremove

USER dryp
# show user effective id and group - it should be non-zero
RUN id

ENV PATH="/home/dryp/.local/bin:${PATH}"

# May need to reinstate these
COPY --chown=dryp:dryp . .
RUN pip install --no-cache-dir --require-hashes --user -r requirements/requirements.txt

# Clear out .exe
RUN find /home/dryp/ -name '*.exe' -exec rm -f {} \;

## Remove GCC
#USER root
#RUN apt-get purge -y --auto-remove gcc
#RUN rm -rf /usr/bin/gcc-10
#USER dryp

# Add profiling stuff
# Install rust
#RUN curl https://sh.rustup.rs -sSf | sh -s -- -y