FROM python:3.7
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list' && wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

RUN apt-get -y update && apt-get -y install ffmpeg exiftool gdal-bin libgdal-dev python3-gdal binutils libproj-dev postgresql-plpython-13
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt
ADD . /code/