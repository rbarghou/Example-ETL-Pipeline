#! /bin/bash


# run alembic migrations
cd /etl/alembic 
alembic upgrade head > /var/log/alembic.log
cd /etl

tail -f /var/log/alembic.log
