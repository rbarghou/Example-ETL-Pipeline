import random
import pytest

from tests.generate import generate

from app.schema import get_ExperimentMeasurement, session_scope, Sample
from app.etl import pipeline


def recursively_get_top_parent(sample):
    """DO NOT USE THIS APPROACH OUTSIDE OF TESTING.  Recursive lookup
    is inefficient.  This approach is used here for the easy of verification
    in the testing context."""
    if sample.parent:
        return recursively_get_top_parent(sample.parent)
    else:
        return sample


# the fresh_database argument is loaded by the pytest fixture system
@pytest.mark.parametrize("n", [1000, 10000, 100000])
def test_pipeline(n, fresh_database):
    """While this test does not follow BDD practices (atomic testing) because
    this tests an ETL pipeline rather than an API or UI, this is appropriate.
    Furthermore, this includes some random sample testing."""
    # Verify initial assumptions
    ExperimentMeasurement = get_ExperimentMeasurement()
    for col in ["ph", "vol"]:
        assert f"measurement_{col}" not in ExperimentMeasurement.__table__.c

    with session_scope() as session:
        assert session.query(ExperimentMeasurement).count() == 0

    generate(n)  # Generate test data
    pipeline()  # Run full etl pipeline

    ExperimentMeasurement = get_ExperimentMeasurement()
    for col in ["ph", "vol"]:
        assert f"measurement_{col}" in ExperimentMeasurement.__table__.c

    with session_scope() as session:
        assert session.query(ExperimentMeasurement).count() >= int(n * .8)

    # Select random ExperimentMeasurements and then recursively verify the
    # correctness of their top parent.  Then verify the presence and
    # correctness of their measurement values.
    random.seed(0)
    for _ in range(50):
        with session_scope() as session:
            measurement = session.query(
                ExperimentMeasurement
            ).get(random.randint(n//10, n))
            sample = session.query(Sample).get(measurement.sample_id)
            top_parent = recursively_get_top_parent(sample)
            assert measurement.top_parent_id == top_parent.id

            for sm in sample.measurements:
                mt = sm.measurement_type
                assert hasattr(measurement, f"measurement_{mt}")
                assert getattr(measurement, f"measurement_{mt}") == sm.value
