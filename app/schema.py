"""This provides schema for the static tables and dynamic tables.
Additionally, there are utilities for session management to cut down on
boilerplate code."""
from contextlib import contextmanager

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    TIMESTAMP,
    VARCHAR,
    DECIMAL,
    create_engine,
)
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker

DBase = declarative_base()

engine = create_engine(
    "mysql+mysqlconnector://etl:asdfasdf@database:3306/etl_db")
Session = sessionmaker()
Session.configure(bind=engine)


@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def inject_session(func):
    """Injects a session context manager into the function decorated as the
    first argument."""
    def wrapped(*args, **kwargs):
        with session_scope() as session:
            func(session, *args, **kwargs)
    return wrapped


class Sample(DBase):
    __tablename__ = "samples"
    id = Column("id", Integer, primary_key=True)
    parent_id = Column("parent_id", ForeignKey("samples.id"))
    children = relationship(
        "Sample", backref=backref("parent", remote_side=[id]))
    experiment = Column("experiment_id", Integer)
    ts = Column("ts", TIMESTAMP)
    measurements = relationship(
        "SampleMeasurement", backref="sample_measurement")

    def __repr__(self):
        return f"<sample id={self.id}" \
               f" timestamp={self.ts}" \
               f" experiment={self.experiment}" \
               f" parent={self.parent_id} />"


class SampleMeasurement(DBase):
    __tablename__ = "sample_measurements"
    sample_id = Column("sample_id", Integer, ForeignKey(
        "samples.id"), primary_key=True)
    measurement_type = Column(
        "measurement_type", VARCHAR(10), primary_key=True)
    value = Column("value", DECIMAL(16, 6))

    def __repr__(self):
        return f"<SampleMeasurement" \
               f" sample_id={self.sample_id}" \
               f" measurement_type={self.measurement_type}" \
               f" value={self.value} />"


def get_ExperimentMeasurement():
    """ExperimentMeasurement is a dynamic model.  It may have new columns
     added to it dynamically. Calling get_ExperimentMeasurement will give
     you a fresh class with the new columns defined. It also uses a fresh
     instance of the automap_base to avoid any conflicts inside that base.

    This must remain a factory design so long as the experiment_measurement
     table must support dynamic column additions"""
    global engine
    ABase = automap_base()
    ABase.prepare(engine, reflect=True)
    return ABase.classes.experiment_measurements
