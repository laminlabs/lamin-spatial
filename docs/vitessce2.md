---
execute_via: python
---

# Vitessce: SpatialData

This tutorial demonstrates how to create interactive Vitessce visualizations for SpatialData objects stored as LaminDB artifacts.
It requires a remote LaminDB instance with cloud storage to enable the Vitessce button (shown below) in the web interface.

<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/dImlJuvjfOhsGD9F0000.png" width="700px">

For visualizing AnnData objects, see the [Vitessce: AnnData](https://docs.lamin.ai/visualization#visualize-an-anndata-object-h5ad-format) guide.

We'll work with spatial transcriptomics data in Zarr, OME-TIFF, and OME-Zarr formats.

```python
# pip install 'vitessce[all]>=3.5.0' lamindb
!lamin connect laminlabs/lamindata  # <-- replace with your remote instance
```

```python
import vitessce as vit
import lamindb as ln

ln.track()
```

## Visualize a SpatialData object (Zarr format)

Here we use an example Visium dataset that has been previously ingested into the public [laminlabs/lamindata](https://lamin.ai/laminlabs/lamindata) instance in this [transform](https://lamin.ai/laminlabs/lamindata/transform/WVB7Q3xLWAnl).

```python
sdata_zarr_artifact = ln.Artifact.get(key="vitessce_examples/visium.sdata.zarr")
```

### Save a VitessceConfig object

You can create a dashboard for one or several datasets by using Vitessce's component API.
Here, we use the [SpatialDataWrapper](https://python-docs.vitessce.io/api_data.html#vitessce.wrappers.SpatialDataWrapper) class to specify which parts of the SpatialData object will be loaded for visualization.

```python
vc = vit.VitessceConfig(
    schema_version="1.0.18",
    description=sdata_zarr_artifact.description,
)

dataset_uid = "sdata_visium"
dataset = vc.add_dataset(name="Breast Cancer Visium", uid=dataset_uid).add_object(
    vit.SpatialDataWrapper(
        sdata_artifact=sdata_zarr_artifact,
        # The following paths are relative to the root of the SpatialData zarr store on-disk.
        image_path="images/CytAssist_FFPE_Human_Breast_Cancer_full_image",
        table_path="tables/table",
        obs_feature_matrix_path="tables/table/X",
        obs_spots_path="shapes/CytAssist_FFPE_Human_Breast_Cancer",
        region="CytAssist_FFPE_Human_Breast_Cancer",
        coordinate_system="global",
        coordination_values={
            # The following tells Vitessce to consider each observation as a "spot"
            "obsType": "spot",
        },
    )
)

# Add views (visualizations) to the configuration:
spatial = vc.add_view("spatialBeta", dataset=dataset)
feature_list = vc.add_view("featureList", dataset=dataset)
layer_controller = vc.add_view("layerControllerBeta", dataset=dataset)

# Initialize visual properties for multiple linked views:
vc.link_views_by_dict(
    [spatial, layer_controller],
    {
        "imageLayer": vit.CoordinationLevel(
            [
                {
                    "photometricInterpretation": "RGB",
                }
            ]
        ),
    },
    scope_prefix=vit.get_initial_coordination_scope_prefix(dataset_uid, "image"),
)
vc.link_views([spatial, layer_controller, feature_list], ["obsType"], ["spot"])

# Layout the views
vc.layout(spatial | (feature_list / layer_controller));
```

Save the `VitessceConfig` object.

```python
sdata_vc_artifact = ln.integrations.save_vitessce_config(
    vc,
    description="View Visium SpatialData Example in Vitessce",
)
```

:::{note}

After running `save_vitessce_config`, a Vitessce button will appear next to the dataset on the [Artifacts](https://lamin.ai/laminlabs/lamindata/artifacts) or [Collections](https://lamin.ai/laminlabs/lamindata/collections) page of the web interface.

If your `VitessceConfig` object references data from multiple artifacts, the Vitessce button will appear next to a `Collection` that groups these artifacts (on the [Collections](https://lamin.ai/laminlabs/lamindata/collections) tab of the Artifacts page).

:::

Clicking the Vitessce button for this [artifact](https://lamin.ai/laminlabs/lamindata/artifact/Z1Q9alE7dBr5lZty) launches an interactive viewer with spatial coordinates, gene expression, and tissue image:

<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/Xl0KgR2dZJHfmn1Q0000.png" width="900px">

## Visualize an image (OME-TIFF format)

Vitesse can visualize data from multiple bioimaging file formats, including [OME-TIFF](https://ome-model.readthedocs.io/en/stable/ome-tiff/).
Again, we use an example dataset that was previously ingested into the [laminlabs/lamindata](https://lamin.ai/laminlabs/lamindata) instance in this [transform](https://lamin.ai/laminlabs/lamindata/transform/WVB7Q3xLWAnl).

```python
ome_tiff_artifact = ln.Artifact.get(
    key="vitessce_examples/VAN0006-LK-2-85-PAS_registered.ome.tif"
)
```

When using OME-TIFF files, we can use [generate-tiff-offsets](https://github.com/hms-dbmi/generate-tiff-offsets) to create an index for the bytes within the OME-TIFF file.
We store these to a companion `.offsets.json` file which makes loading subsets of the image more efficient.
We use a pre-generated file generated in the [transform](https://lamin.ai/laminlabs/lamindata/transform/WVB7Q3xLWAnl) above.

```python
offsets_artifact = ln.Artifact.get(
    key="vitessce_examples/VAN0006-LK-2-85-PAS_registered.offsets.json"
)
```

### Save a VitessceConfig object

You can create a dashboard for one or several datasets by using Vitessce's component API.

Here, we use the [ImageOmeTiffWrapper](https://python-docs.vitessce.io/api_data.html#vitessce.wrappers.ImageOmeTiffWrapper) class to specify which pair of OME-TIFF file and offsets JSON file to load.

```python
vc = vit.VitessceConfig(
    schema_version="1.0.18", description=ome_tiff_artifact.description
)

dataset = vc.add_dataset("Image").add_object(
    vit.ImageOmeTiffWrapper(
        img_artifact=ome_tiff_artifact,
        offsets_artifact=offsets_artifact,
    )
)

spatial = vc.add_view("spatialBeta", dataset=dataset)
layer_controller = vc.add_view("layerControllerBeta", dataset=dataset)
vc.layout(spatial | layer_controller);
```

Save the `VitessceConfig` object.

```python
ome_tiff_vc_artifact = ln.integrations.save_vitessce_config(
    vc,
    description="View PAS OME-TIFF, Neumann et al., 2020 in Vitessce",
)
```

:::{note}

After running `save_vitessce_config`, a Vitessce button will appear next to the dataset on the [Artifacts](https://lamin.ai/laminlabs/lamindata/artifacts) or [Collections](https://lamin.ai/laminlabs/lamindata/collections) page of the web interface.

If your `VitessceConfig` object references data from multiple artifacts, the Vitessce button will appear next to a `Collection` that groups these artifacts (on the [Collections](https://lamin.ai/laminlabs/lamindata/collections) tab of the Artifacts page).

In the case of OME-TIFF, the presence of the corresponding offsets JSON file will result in the creation of a Collection.

:::

Clicking the Vitessce button for this [collection](https://aws.us-east-1.laminhub.com/laminlabs/lamindata/collection/DMF53hCJZQdnVIzT) launches an interactive tissue image viewer:

<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/qECYBXyOgHiEJj3l0000.png" width="900px">

## Visualize an image (OME-Zarr format)

We retrieve an OME-Zarr (also known as OME-NGFF) formatted image that was [ingested](https://lamin.ai/laminlabs/lamindata/transform/WVB7Q3xLWAnl) into [laminlabs/lamindata](https://lamin.ai/laminlabs/lamindata) alongside the previous datasets.

```python
ome_zarr_artifact = ln.Artifact.get(key="vitessce_examples/visium.ome.zarr")
```

### Save a VitessceConfig object

You can create a dashboard for one or several datasets by using Vitessce's component API.
Here, we use the [ImageOmeZarrWrapper](https://python-docs.vitessce.io/api_data.html#vitessce.wrappers.ImageOmeZarrWrapper) class to specify an OME-Zarr file to load for visualization.

```python
vc = vit.VitessceConfig(
    schema_version="1.0.18", description=ome_zarr_artifact.description
)

dataset_uid = "ome_zarr_image"
dataset = vc.add_dataset("Image", uid=dataset_uid).add_object(
    vit.ImageOmeZarrWrapper(
        img_artifact=ome_zarr_artifact,
    )
)

spatial = vc.add_view("spatialBeta", dataset=dataset)
layer_controller = vc.add_view("layerControllerBeta", dataset=dataset)
vc.link_views_by_dict(
    [spatial, layer_controller],
    {
        "imageLayer": vit.CoordinationLevel(
            [
                {
                    "photometricInterpretation": "RGB",
                }
            ]
        ),
    },
    scope_prefix=vit.get_initial_coordination_scope_prefix(dataset_uid, "image"),
)
vc.layout(spatial | layer_controller);
```

Save the `VitessceConfig` object.

```python
ome_zarr_vc_artifact = ln.integrations.save_vitessce_config(
    vc,
    description="View Visium OME-Zarr Example in Vitessce",
)
```

:::{note}

After running `save_vitessce_config`, a Vitessce button will appear next to the dataset on the [Artifacts](https://lamin.ai/laminlabs/lamindata/artifacts) or [Collections](https://lamin.ai/laminlabs/lamindata/collections) page of the web interface.

If your `VitessceConfig` object references data from multiple artifacts, the Vitessce button will appear next to a `Collection` that groups these artifacts (on the [Collections](https://lamin.ai/laminlabs/lamindata/collections) tab of the Artifacts page).

:::

Clicking the Vitessce button for this [artifact](https://lamin.ai/laminlabs/lamindata/artifact/Z1Q9alE7dBr5lZty) launches an interactive tissue image viewer:

<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/guM5RoXCgR65MThV0000.png" width="900px">

```python
# compare the generated vitessce config to the public one (SpatialData) on vitessce/examples
db = ln.DB("vitessce/examples")
public_vc_json = db.Artifact.get("Xot2a5ZAcTW3fClG0000").load()
sdata_vc_json = sdata_vc_artifact.load()

assert public_vc_json["layout"] == sdata_vc_json["layout"]
assert public_vc_json["coordinationSpace"] == sdata_vc_json["coordinationSpace"]

# compare the generated vitessce config json to the public one (OME-TIFF) on vitessce/examples
public_vc_json = db.Artifact.get("QtF1OEtYyUe1EQ1k0000").load()
ome_tiff_vc_json = ome_tiff_vc_artifact.load()
assert public_vc_json["layout"] == ome_tiff_vc_json["layout"]
assert public_vc_json["coordinationSpace"] == ome_tiff_vc_json["coordinationSpace"]

# compare the generated vitessce config to the public one (OME-Zarr) on vitessce/examples
public_vc_json = db.Artifact.get("cjvX6EFrdSwsxOQl0000").load()
ome_zarr_vc_json = ome_zarr_vc_artifact.load()

assert public_vc_json["layout"] == ome_zarr_vc_json["layout"]
assert public_vc_json["coordinationSpace"] == ome_zarr_vc_json["coordinationSpace"]
```

```python
ln.finish()
```
