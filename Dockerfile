FROM python:2.7

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY setup/requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app
ENTRYPOINT ["uwsgi", "run/api-dev-uwsgi.ini"]
