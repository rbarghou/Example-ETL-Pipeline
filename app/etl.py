"""
This pipeline moves data from the samples and sample_measurements table
into the experiment_measurement table.

This requires 5 steps:
* add_measurement_columns
* add_samples_and_experiments
* add_values
* set_top_parents_of_root_nodes
* set_top_parents_adjacent

Future work involves assigning each of these functions to Airflow Operators.

The DAG for such airflow operators should look like this:
    [add_measurement_columns, add_samples_and_experiments]
    >> add_values
    >> set_top_parents_of_root_nodes
    >> set_top_parents_adjacent
"""
from alembic.runtime.migration import MigrationContext
from alembic.operations import Operations

from sqlalchemy import insert, Column, DECIMAL, update, join, select

from app.schema import (
    inject_session,
    Sample,
    SampleMeasurement,
    get_ExperimentMeasurement,
)


@inject_session
def add_measurement_columns(session):
    """Inspects all SampleMeasurements finding distinct values for
    measurement_types, then creates new columns in the ExperimentMeasurement
    table using an Alembic migration context."""
    # TODO: Consider index on SampleMeasurement.measurement_types.
    ExperimentMeasurement = get_ExperimentMeasurement()
    measurement_types = session.query(
        SampleMeasurement.measurement_type
    ).distinct().all()
    measurement_types = sorted([_ for (_, ) in measurement_types])

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


@inject_session
def add_samples_and_experiments(session):
    """Finds all samples that do not have ExperimentMeasurement entries
    associated with them and then creates the relevant entries.  It only
    populates the sample_id and the experiment_id."""
    ExperimentMeasurement = get_ExperimentMeasurement()
    sample_subquery = (
        session.query(
            Sample.id,
            Sample.experiment
        ).filter(
            ~Sample.id.in_(
                session.query(
                    ExperimentMeasurement.sample_id
                )
            )
        )
    )
    fields = [
        ExperimentMeasurement.sample_id,
        ExperimentMeasurement.experiment_id
    ]
    insert_stmt = insert(
        ExperimentMeasurement
    ).from_select(fields, sample_subquery)

    session.execute(insert_stmt)
    session.commit()


@inject_session
def add_values(session):
    """Gets values form the SampleMeasurement table for all new
    ExperimentMeasurements.  This new values are assumed to be ones that
    do not yet have their top_parent set."""
    ExperimentMeasurement = get_ExperimentMeasurement()
    new_measurements = session.query(
        ExperimentMeasurement.sample_id
    ).filter(ExperimentMeasurement.top_parent_id.is_(None))

    # NOTE:  In production code this would be changed to a logger
    print(f"Populating {new_measurements.count()} new measurements")

    # This is the only query that should incur network traffic in this step
    measurement_types = session.query(
        SampleMeasurement.measurement_type
    ).filter(
        SampleMeasurement.sample_id.in_(new_measurements)
    ).distinct()

    # By populating the values by measurement type, it is possible to do
    #  all the value copying in the database without incurring any network
    #  with data in it.  This should be acceptable assuming that the number
    #  of measurement_types is proportional to the log of the number of
    #  measurements or lower.
    for (mt,) in measurement_types:
        print(f"Populating values for {mt} measurement_type")
        measurement_values = select([
            SampleMeasurement.sample_id,
            SampleMeasurement.value
        ]).where(
            SampleMeasurement.measurement_type == mt
        ).alias()

        update_stmt = update(
            ExperimentMeasurement
        ).where(
            ExperimentMeasurement.sample_id
            ==
            measurement_values.columns.sample_id
        ).values(**{f"measurement_{mt}": measurement_values.columns.value})

        session.execute(update_stmt)
        session.commit()


@inject_session
def set_top_parents_of_root_nodes(session):
    """Sets top parent values over experiment_measurements whose sample has no
    parent.  These are experiment_measurements whose top parent is also its
    sample."""
    ExperimentMeasurement = get_ExperimentMeasurement()
    root_samples = session.query(ExperimentMeasurement.sample_id).filter(
        ExperimentMeasurement.sample_id == Sample.id,
        ExperimentMeasurement.top_parent_id.is_(None),
        Sample.parent_id.is_(None)
    )
    update_stmt = update(ExperimentMeasurement).where(
        ExperimentMeasurement.sample_id.in_(root_samples)
    ).values(
        top_parent_id=ExperimentMeasurement.sample_id
    )
    session.execute(update_stmt)
    session.commit()


@inject_session
def set_top_parents_adjacent(session):
    """Iteratively sets the top parents of experiment_measurements whose
    samples have parents with top parents.  This should be able to handle
    deeper trees than the specification requires."""
    ExperimentMeasurement = get_ExperimentMeasurement()
    subquery = select([
        Sample.id,
        ExperimentMeasurement.top_parent_id
    ]).select_from(
        join(
            Sample,
            ExperimentMeasurement,
            Sample.parent_id == ExperimentMeasurement.sample_id
        )
    ).where(ExperimentMeasurement.top_parent_id.isnot(None)).alias()

    update_stmt = update(ExperimentMeasurement).where(
        ExperimentMeasurement.sample_id == subquery.columns.id
    ).values(top_parent_id=subquery.columns.top_parent_id)

    ems_with_no_top_parent = (
        session
        .query(ExperimentMeasurement)
        .filter(ExperimentMeasurement.top_parent_id.is_(None))
    )
    while ems_with_no_top_parent.count():
        session.execute(update_stmt)
        session.commit()


def pipeline():
    """This runs the entire etl pipeline as one series of function calls."""
    add_measurement_columns()
    add_samples_and_experiments()
    add_values()
    set_top_parents_of_root_nodes()
    set_top_parents_adjacent()


if __name__ == "__main__":
    pipeline()
