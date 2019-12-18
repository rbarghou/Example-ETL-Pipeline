"""
This file represents my first approach.  I ended up rejecting this approach
 because I decided that it would be desirable to push more of the logic
 into the sql scripts themselves.  This would reduce network traffic to and
 from the mysql server.
"""

from collections import defaultdict

from alembic.runtime.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Column, DECIMAL
from sqlalchemy.sql.expression import update

from app.schema import (
    Sample,
    SampleMeasurement,
    get_ExperimentMeasurement,
    session_scope
)


def add_measurement_columns(start: int, end: int, session):
    assert start <= end

    ExperimentMeasurement = get_ExperimentMeasurement()
    # Get all the distinct measurement types in the batch that this function
    #  call is responsible for extracting
    measurement_types = sorted([
        _ for (_,) in session.query(
            SampleMeasurement.measurement_type
        ).filter(
            SampleMeasurement.sample_id >= start,
            SampleMeasurement.sample_id <= end
        ).distinct().all()  # Don't transmit any more than you have to.
    ])
    cols = set([f"measurement_{mt}" for mt in measurement_types])
    new_cols = cols - set(ExperimentMeasurement.__table__.columns.keys())
    if new_cols:
        ctx = MigrationContext.configure(session.connection())
        op = Operations(ctx)
        for new_col in new_cols:
            print(f"creating new_col: {new_col}")
            op.add_column(
                "experiment_measurements",
                Column(new_col, DECIMAL(16, 6))
            )


def add_update_measurement(start, end, session):
    ExperimentMeasurement = get_ExperimentMeasurement()

    # Get all the sample measurements for the sample id range
    sample_measurements = (
        session.query(
            SampleMeasurement.sample_id,
            SampleMeasurement.measurement_type,
            SampleMeasurement.value,
        )
        .filter(SampleMeasurement.sample_id >= start)
        .filter(SampleMeasurement.sample_id <= end)
    )

    # Flatten the measurement types (i.e. pivot the data)
    experiment_measurement_dicts = defaultdict(dict)
    for sample_id, measurement_type, value in sample_measurements:
        experiment_measurement_dicts[sample_id][
            f"measurement_{measurement_type}"
        ] = value

    # Get the experiment measurements that are already in the database
    # for this range. These will be updated rather than inserted.
    existing_sample_ids = [
        sample_id
        for (sample_id,) in session.query(ExperimentMeasurement.sample_id)
        .filter(ExperimentMeasurement.sample_id >= start)
        .filter(ExperimentMeasurement.sample_id <= end)
        .all()
    ]

    # Bulk update ExperimentMeasurement
    mappings = []
    for sample_id in existing_sample_ids:
        mapping = {"sample_id": sample_id}
        for measurement_col, measurement_val in experiment_measurement_dicts[
            sample_id
        ].items():
            mapping[measurement_col] = measurement_val
        mappings.append(mapping)
    session.bulk_update_mappings(ExperimentMeasurement, mappings)

    # Bulk add remaining values to ExperimentMeasurements
    mappings = []
    for sample_id in set(experiment_measurement_dicts.keys()) - set(
        existing_sample_ids
    ):
        mapping = {"sample_id": sample_id}
        for measurement_col, measurement_val in experiment_measurement_dicts[
            sample_id
        ].items():
            mapping[measurement_col] = measurement_val
        mappings.append(mapping)
    session.bulk_insert_mappings(ExperimentMeasurement, mappings)


def update_experiment(start, end, session):
    ExperimentMeasurement = get_ExperimentMeasurement()
    _sample_id = ExperimentMeasurement.sample_id
    session.execute(
        update(
            ExperimentMeasurement
        ).where(
            _sample_id == Sample.id
            and start <= _sample_id <= end
        ).values(experiment_id=Sample.experiment)
    )


def pipeline(start, end):
    with session_scope() as session:
        add_measurement_columns(start, end, session)
    with session_scope() as session:
        add_update_measurement(start, end, session)
    with session_scope() as session:
        update_experiment(start, end, session)


raise DeprecationWarning(
    "etl_app_side is deprecated.  It remains as demonstration of an initial "
    "approach to using the more python focused etl steps.  If it's determined "
    "that the SQL approach locks the database too much or creates too much "
    "risk or requires too much locking, then this approach can be revisited "
    "as a potential solution."
)
