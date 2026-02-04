---
execute_via: python
---

# Vitessce: AnnData

This tutorial demonstrates how to use Vitessce to create interactive visualizations for data stored as LaminDB artifacts. It requires a remote LaminDB instance with cloud storage to enable the Vitessce button (shown below) in the web interface.

<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/tIUr8SDgC0svqXW60001.png" width="700px">

It has been adapted from the data preparation examples in [the Vitessce documentation](https://vitessce.github.io/vitessce-python).

In this part, we'll visualize an AnnData object stored in both H5AD and Zarr formats.

```python
# pip install 'vitessce[all]>=3.5.0' lamindb
!lamin connect laminlabs/lamindata # <-- replace with your remote instance
```

```python
import vitessce as vit
import lamindb as ln

ln.track()
```

## Visualize an AnnData object (H5AD format)

Here we use the Habib et al. 2017 dataset from the [COVID-19 Cell Atlas](https://www.covid19cellatlas.org/index.healthy.html#habib17) that has been previously subset to highly variable genes.
It was ingested into the public [laminlabs/lamindata](https://lamin.ai/laminlabs/lamindata) instance in this [transform](https://lamin.ai/laminlabs/lamindata/transform/HuFKHbJ5DxKt).

```python
h5ad_artifact = ln.Artifact.get(key="vitessce_examples/habib17.h5ad")
```

When using `.h5ad` files, we construct a [Reference Specification](https://fsspec.github.io/kerchunk/spec.html) which enables interoperability with the [Zarr](https://zarrita.dev/packages/storage.html#referencestore) interface.
The Reference Specification JSON was also generated in the [transform](https://lamin.ai/laminlabs/lamindata/transform/HuFKHbJ5DxKt) above.

```python
ref_artifact = ln.Artifact.get(key="vitessce_examples/habib17.reference.json")
```

### Save a VitessceConfig object

You can create a dashboard for one or several datasets by using Vitessce's component API.

You can pass artifacts to the `AnnDataWrapper` class using the `adata_artifact` and `ref_artifact` [parameters](https://python-docs.vitessce.io/api_data.html#vitessce.wrappers.AnnDataWrapper).

```python
vc = vit.VitessceConfig(
    schema_version="1.0.18",
    description=h5ad_artifact.description,
)

dataset = vc.add_dataset(name="Habib 2017").add_object(
    vit.AnnDataWrapper(
        adata_artifact=h5ad_artifact,
        ref_artifact=ref_artifact,
        obs_feature_matrix_path="X",
        obs_embedding_paths=["obsm/X_umap"],
        obs_embedding_names=["UMAP"],
        obs_set_paths=["obs/CellType"],
        obs_set_names=["Cell Type"],
    )
)

obs_sets = vc.add_view(vit.ViewType.OBS_SETS, dataset=dataset)
obs_sets_sizes = vc.add_view(vit.ViewType.OBS_SET_SIZES, dataset=dataset)
scatterplot = vc.add_view(vit.ViewType.SCATTERPLOT, dataset=dataset, mapping="UMAP")
heatmap = vc.add_view(vit.ViewType.HEATMAP, dataset=dataset)
genes = vc.add_view(vit.ViewType.FEATURE_LIST, dataset=dataset)
vc.link_views([scatterplot, heatmap], ["featureValueColormapRange"], [[0.0, 0.1]])
vc.layout(((scatterplot | obs_sets) / heatmap) | (obs_sets_sizes / genes))
```

Save the `VitessceConfig` object.

```python
h5ad_vc_artifact = ln.integrations.save_vitessce_config(
    vc,
    description="View Habib17 (h5ad) in Vitessce",
)
```

:::{note}

After running `save_vitessce_config`, a Vitessce button will appear next to the dataset on the [Artifacts](https://lamin.ai/laminlabs/lamindata/artifacts) or [Collections](https://lamin.ai/laminlabs/lamindata/collections) page of the web interface.

If your `VitessceConfig` object references data from multiple artifacts, the Vitessce button will appear next to a `Collection` that groups these artifacts (on the [Collections](https://lamin.ai/laminlabs/lamindata/collections) tab of the Artifacts page).

Note that when using an `.h5ad`-based artifact, the presence of the corresponding `.reference.json` file will result in the creation of a Collection.

:::

The Vitessce button for this dataset is available on the [Collection](https://lamin.ai/laminlabs/lamindata/collection/H1AlT19wFq7HdHqZ) page.

## Visualize an AnnData object (Zarr format)

AnnData objects can be saved on-disk to not only `.h5ad` files, but also to [Zarr stores](https://zarr.readthedocs.io/en/stable/tutorial.html#storage-alternatives) using AnnData's [write_zarr](https://anndata.readthedocs.io/en/latest/generated/anndata.AnnData.write_zarr.html) method.

Just like in the above section, we use a zarr storage that has been previously written with `write_zarr()` and subset to highly variable genes and ingested into the `vitessce/examples` instance.

```python
adata_zarr_artifact = ln.Artifact.get(key="vitessce_examples/habib17.adata.zarr")
```

### Save a VitessceConfig object

You can create a dashboard for one or several datasets by using Vitessce's component API.
Here, we configure the visualization the same way as above in the `.h5ad`-based example, with the exception of the `ref_artifact` parameter, as `.zarr`-based AnnData objects do not require a Reference Specification for Zarr interoperability.

```python
vc = vit.VitessceConfig(
    schema_version="1.0.18",
    description=adata_zarr_artifact.description,
)

dataset = vc.add_dataset(name="Habib 2017").add_object(
    vit.AnnDataWrapper(
        adata_artifact=adata_zarr_artifact,
        obs_feature_matrix_path="X",
        obs_embedding_paths=["obsm/X_umap"],
        obs_embedding_names=["UMAP"],
        obs_set_paths=["obs/CellType"],
        obs_set_names=["Cell Type"],
    )
)

obs_sets = vc.add_view(vit.Component.OBS_SETS, dataset=dataset)
obs_sets_sizes = vc.add_view(vit.Component.OBS_SET_SIZES, dataset=dataset)
scatterplot = vc.add_view(vit.Component.SCATTERPLOT, dataset=dataset, mapping="UMAP")
heatmap = vc.add_view(vit.Component.HEATMAP, dataset=dataset)
genes = vc.add_view(vit.Component.FEATURE_LIST, dataset=dataset)

vc.link_views([scatterplot, heatmap], ["featureValueColormapRange"], [[0.0, 0.1]])
vc.layout(((scatterplot | obs_sets) / heatmap) | (obs_sets_sizes / genes))
```

Save the `VitessceConfig` object.

```python
adata_zarr_vc_artifact = ln.integrations.save_vitessce_config(
    vc,
    description="View Habib17 in Vitessce",
)
```

:::{note}

After running `save_vitessce_config`, a Vitessce button will appear next to the dataset on the [Artifacts](https://lamin.ai/laminlabs/lamindata/artifacts) or [Collections](https://lamin.ai/laminlabs/lamindata/collections) page of the web interface.

If your `VitessceConfig` object references data from multiple artifacts, the Vitessce button will appear next to a `Collection` that groups these artifacts (on the [Collections](https://lamin.ai/laminlabs/lamindata/collections) tab of the Artifacts page).

:::

Clicking the Vitessce button for this [Artifact](https://lamin.ai/laminlabs/lamindata/artifact/Ljx9cSOxELkGisVt) (`.zarr`-based) or [Collection](#visualize-an-anndata-object-h5ad-format) (`.h5ad`-based) launches the same interactive viewer, as both formats represent the same dataset here:

<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/6bYCczExolBzBiQH0002.png" width="900px">

```python
# compare the generated vitessce config to the public one on vitessce/examples (H5AD)
db = ln.DB("vitessce/examples")
public_vc_json = db.Artifact.get("ffUKrGJGNHL3TDhG0000").load()
h5ad_vc_json = h5ad_vc_artifact.load()

assert public_vc_json["layout"] == h5ad_vc_json["layout"]
assert public_vc_json["coordinationSpace"] == h5ad_vc_json["coordinationSpace"]

# compare the generated vitessce config to the public one on vitessce/examples (Zarr)
public_vc_json = db.Artifact.get("J4tMB6qAeHvsgEsp0000").load()
adata_zarr_vc_json = adata_zarr_vc_artifact.load()

assert public_vc_json["layout"] == adata_zarr_vc_json["layout"]
assert public_vc_json["coordinationSpace"] == adata_zarr_vc_json["coordinationSpace"]
```

```python
ln.finish()
```
