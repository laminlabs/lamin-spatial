import bionty as bt
import lamindb as ln
import pandas as pd
import pytest
from spatialdata.datasets import blobs


@pytest.fixture
def blobs_data():
    sdata = blobs()

    sdata.tables["table"].var.index = [
        "ENSG00000139618",  # BRCA2
        "ENSG00000157764",  # BRAF
        "ENSG00000999999",  # does not exist - to test add_new_from_var_index
    ]
    sdata.tables["table"].obs["region"] = pd.Categorical(
        ["region 1"] * 13 + ["region 2"] * 13
    )
    sdata.attrs["sample"] = {
        "assay": "VisiumHD",
        "disease": "Alzheimer's dementia",
        "developmental_stage": "very early",
    }

    return sdata


def test_spatialdata_curator(setup_instance, blobs_data):
    from lamin_spatial import SpatialDataCurator
    from lamindb.core.exceptions import ValidationError

    with pytest.raises(
        ValidationError, match="key passed to categoricals is not present"
    ):
        SpatialDataCurator(
            blobs_data,
            var_index={"table": bt.Gene.ensembl_gene_id},
            categoricals={
                "sample": {
                    "does not exist": bt.ExperimentalFactor.name,
                },
            },
            organism="human",
        )

    with pytest.raises(ValidationError, match="key passed to sources is not present"):
        SpatialDataCurator(
            blobs_data,
            var_index={"table": bt.Gene.ensembl_gene_id},
            categoricals={
                "table": {"region": ln.ULabel.name},
            },
            sources={"sample": {"whatever": bt.CellLine.name}},
            organism="human",
        )

    curator = SpatialDataCurator(
        blobs_data,
        var_index={"table": bt.Gene.ensembl_gene_id},
        categoricals={
            "sample": {
                "assay": bt.ExperimentalFactor.name,
                "disease": bt.Disease.name,
                "developmental_stage": bt.DevelopmentalStage.name,
            },
            "table": {"region": ln.ULabel.name},
        },
        organism="human",
    )

    curator.validate()

    curator.add_new_from_var_index("table")
    curator.add_new_from(key="developmental_stage", accessor="sample")
    curator.add_new_from(key="region", accessor="table")

    curator.standardize(key="disease", accessor="sample")

    artifact = curator.save_artifact(description="blob spatialdata")

    artifact.describe()

    # clean up
    artifact.delete(permanent=True)
    ln.ULabel.filter().delete()
    bt.ExperimentalFactor.filter().delete()
    bt.Disease.filter().delete()
    bt.DevelopmentalStage.filter().delete()
    bt.Gene.filter().delete()
    ln.FeatureSet.filter().delete()
    ln.Feature.filter().delete()
