FROM python:3.11

COPY ./app /app
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN  apt-get update \
  && apt-get -y install gcc postgresql nano software-properties-common python3-launchpadlib \
  && add-apt-repository ppa:openjdk-r/ppa \
  && apt-get update \
  && apt-get -y install curl openjdk-11-jdk \
  && apt-get clean

# install python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD tail /dev/null -f
