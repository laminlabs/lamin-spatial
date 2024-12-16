import lamindb_setup as ln_setup
import pytest


@pytest.fixture(scope="module")
def setup_instance():
    ln_setup.init(storage="./testdb", schema="bionty,wetlab")
    yield
    ln_setup.delete("testdb", force=True)
