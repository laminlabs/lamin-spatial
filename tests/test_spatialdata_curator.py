import pytest
from spatialdata.datasets import blobs


@pytest.fixture
def blobs_data():
    sdata = blobs()
    sdata.attrs["sample"] = {
        "assay": "VisiumHD",
        "disease": "Alzheimer disease",
        "preproc_version": "Space Ranger version 3.0.0",
    }
    return sdata


def test_spatialdata_creation():
    pass


def test_spatialdata_curate():
    pass


def test_spatial_standardize():
    pass


def test_add_new_from_var_index():
    pass


def test_add_new_from():
    pass


def test_save_artifact():
    pass
