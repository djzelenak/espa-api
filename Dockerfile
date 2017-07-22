FROM python:2.7

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY setup/requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /home/espadev/.usgs/
RUN ln -s /usr/src/app/run/config.ini /home/espadev/.usgs/.cfgnfo

COPY . /usr/src/app

RUN mkdir -p /var/log/uwsgi/
EXPOSE 4004
ENTRYPOINT ["uwsgi", "run/api-dev-uwsgi.ini"]
