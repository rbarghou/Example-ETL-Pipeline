import random
from app.schema import Sample, SampleMeasurement, inject_session


measurement_types = [
    "smoot",
    "foo",
    "bar",
    "len",
    "area"
]


@inject_session
def generate(session, k):
    """Generates random data with a fixed seed.  This is done in 2 steps.

    Step 1: Create k new Sample instances are generated with a random
    experiment_id and a random parent from the previous 100 samples and with
    a 5% chance of being a top sample.

    Step 2: Create new SampleMeasurement instances for the new samples.
    This creates a measurement of each different type with fixed probabilities
    with novel types coming from the measurement_types list."""
    random.seed(0)
    samples = []
    for n in range(2, k):
        if random.random() > .95:
            parent = None
        else:
            parent = random.randint(max(n - 100, 1), n)
        experiment = (n % 20) + int(n / 1000) + 1
        samples.append({
            "experiment": experiment,
            "parent_id": parent
        })
    session.bulk_insert_mappings(Sample, samples)
    session.commit()

    existing_measurements = session.query(SampleMeasurement.sample_id)
    new_sample_ids = (
        session.query(Sample.id)
        .filter(~Sample.id.in_(existing_measurements))
        .filter(Sample.id > 20)
    )
    sample_measurements = []
    for (sample_id, ) in new_sample_ids:
        if random.random() < .95:
            sample_measurements.append({
                "sample_id": sample_id,
                "measurement_type": "vol",
                "value": random.random() * 100
            })
        if random.random() < .7:
            sample_measurements.append({
                "sample_id": sample_id,
                "measurement_type": "ph",
                "value": random.random() * 100
            })
        if random.random() < .2:
            sample_measurements.append({
                "sample_id": sample_id,
                "measurement_type": random.choice(measurement_types),
                "value": 1
            })

    session.bulk_insert_mappings(SampleMeasurement, sample_measurements)
    session.commit()
