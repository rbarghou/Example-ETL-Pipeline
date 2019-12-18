FROM python:3.8

ADD . /etl

WORKDIR /etl

RUN pip install alembic==1.3.1 && \
    pip install pytest==5.3.1 && \
    pip install mysql-connector-python==8.0.18 && \
    touch /var/log/alembic.log && \
    alembic init alembic && \
    mv alembic.ini ./alembic/alembic.ini && \
    mv -f versions /etl/alembic/versions

ENTRYPOINT ./entrypoint.sh
