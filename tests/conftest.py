import subprocess
from pytest import fixture


@fixture
def fresh_database():
    subprocess.check_call(["./scripts/recreate_database.sh"])
