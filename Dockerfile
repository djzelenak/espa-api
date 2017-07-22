FROM python:2.7

RUN mkdir -p /home/espadev/espa-api
WORKDIR /home/espadev/espa-api

COPY setup/requirements.txt /home/espadev/espa-api
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /home/espadev/.usgs/
RUN ln -s /usr/src/app/run/config.ini /home/espadev/.usgs/.cfgnfo

COPY . /home/espadev/espa-api

EXPOSE 4004
ENTRYPOINT ["uwsgi", "run/api-dev-uwsgi.ini"]
