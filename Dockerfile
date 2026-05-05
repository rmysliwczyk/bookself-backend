FROM python:3.13-slim-trixie

WORKDIR /

#COPY ./alembic.ini /
COPY ./app /app
COPY ./.env /.env
COPY ./requirements.txt /requirements.txt
copy ./start_script.sh /

VOLUME /app/database

RUN pip install -r requirements.txt
ENTRYPOINT ["./start_script.sh"]
