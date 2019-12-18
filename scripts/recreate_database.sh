#! /bin/bash

pushd /etl/alembic

alembic downgrade base
alembic upgrade head

# In case this is sourced rather than executed
popd
