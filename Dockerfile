FROM python:3.7
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
RUN apt-get -y update && apt-get -y install ffmpeg exiftool gdal-bin libgdal-dev python3-gdal binutils libproj-dev postgresql-plpython-13
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt
ADD . /code/