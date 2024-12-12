from typing import Any, Iterable, MutableMapping

import lamindb_setup as ln_setup
import pandas as pd
from lamin_utils import colors, logger
from lamindb._curate import (
    AnnDataCurator,
    CurateLookup,
    DataFrameCurator,
    _ref_is_name,
    check_registry_organism,
    get_current_filter_kwargs,
)
from lamindb.core._data import add_labels
from lamindb.core._feature_manager import parse_feature_sets_from_anndata
from lamindb.core._settings import settings
from lamindb.core.exceptions import ValidationError
from lnschema_core import Artifact, Collection, Feature, FeatureSet, Record, Run
from lnschema_core.types import FieldAttr
from spatialdata import SpatialData


class SpatialDataCurator:
    """Curation flow for a ``Spatialdata`` object.

    See also :class:`~lamindb.Curator`.

    Note that if genes or other measurements are removed from the SpatialData object,
    the object should be recreated using :meth:`~lamindb.Curator.from_spatialdata`.

    In the following docstring, an accessor refers to either a ``.table`` or the sample level metadata.

    Args:
        sdata: The SpatialData object to curate.
        var_index: A dictionary mapping table keys to the ``.var`` indices.
        categoricals: A nested dictionary mapping an accessor to dictionaries that map columns to a registry field.
            The key 'sample' must be used for sample level metadata that is stored in the Spatialdata object and not one of the tables.
        using_key: A reference LaminDB instance.
        verbosity: The verbosity level.
        organism: The organism name.
        sources: A dictionary mapping an accessor to dictionaries that map columns to Source records.
        exclude: A dictionary mapping an accessor to dictionaries of column names to values to exclude from validation.
            When specific :class:`~bionty.Source` instances are pinned and may lack default values (e.g., "unknown" or "na"),
            using the exclude parameter ensures they are not validated.

    Examples:
        >>> import bionty as bt
        >>> curator = ln.Curator.from_spatialdata(
        ...     sdata,
        ...     var_index={
        ...         "table_1": bt.Gene.ensembl_gene_id,
        ...     },
        ...     categoricals={
        ...         "table1":
        ...             {"cell_type_ontology_id": bt.CellType.ontology_id, "donor_id": ln.ULabel.name},
        ...         "sample":
        ...             {"experimental_factor": bt.ExperimentalFactor.name},
        ...     },
        ...     organism="human",
        ... )
    """

    def __init__(
        self,
        sdata: SpatialData,
        var_index: dict[str, FieldAttr],
        categoricals: dict[str, dict[str, FieldAttr]] | None = None,
        using_key: str | None = None,
        verbosity: str = "hint",
        organism: str | None = None,
        sources: dict[str, dict[str, Record]] | None = None,
        exclude: dict[str, dict] | None = None,
    ) -> None:
        if sources is None:
            sources = {}
        self._sources = sources
        if exclude is None:
            exclude = {}
        self._exclude = exclude
        self._sdata = sdata
        self._kwargs = {"organism": organism} if organism else {}
        self._var_fields = var_index
        self._verify_accessor(self._var_fields.keys())
        self._categoricals = categoricals  # TODO Verify existence and no overlap
        self._tables = set(self._var_fields.keys()) | set(
            self._categoricals.keys() - {"sample"}
        )
        self._using_key = using_key
        self._verbosity = verbosity
        self._sample_df_curator = None
        self._sample_metadata = self._sdata.get_attrs(
            key="spatialdata-db", return_as="df", flatten=True
        )  # this key will need to be adapted in the future

        if "sample" in self._categoricals.keys():
            self._sample_df_curator = DataFrameCurator(
                df=self._sample_metadata,
                columns=Feature.name,
                categoricals=self._categoricals.get("sample", {}),
                using_key=using_key,
                verbosity=verbosity,
                sources=self._sources.get("sample"),
                exclude=self._exclude.get("sample"),
                check_valid_keys=False,
                **self._kwargs,
            )
        self._table_adata_curators = {
            table: AnnDataCurator(
                data=sdata[table],
                var_index=var_index.get(table),
                categoricals=self._categoricals.get(table),
                using_key=using_key,
                verbosity=verbosity,
                sources=self._sources.get(table),
                exclude=self._exclude.get(table),
                **self._kwargs,
            )
            for table in self._tables
        }
        self._non_validated = None

    @property
    def var_index(self) -> FieldAttr:
        """Return the registry field to validate variables index against."""
        return self._var_fields

    @property
    def categoricals(self) -> dict[str, dict[str, FieldAttr]]:
        """Return the categoricals fields to validate against."""
        return self._categoricals

    @property
    def non_validated(self) -> dict[str, dict[str, list[str]]]:
        """Return the non-validated features and labels."""
        if self._non_validated is None:
            raise ValidationError("Please run validate() first!")
        return self._non_validated

    def _verify_accessor(self, accessors: Iterable[str]):
        """Verify that the accessors exist."""
        for acc in accessors:
            if (
                self._sdata.get_attrs(key=acc) is None
                and acc not in self._sdata.tables.keys()
            ):
                raise ValidationError(f"Accessor '{acc} does not exist!")

    def lookup(
        self, using_key: str | None = None, public: bool = False
    ) -> CurateLookup:
        """Lookup categories.

        Args:
            using_key: The instance where the lookup is performed.
                if "public", the lookup is performed on the public reference.
        """
        return CurateLookup(
            categoricals=self.categoricals,
            slots={
                **{f"{k}_var_index": v for k, v in self._var_fields.items()},
            },
            using_key=using_key or self._using_key,
            public=public,
        )

    def _update_registry_all(self):
        """Update all registries."""
        if self._sample_df_curator is not None:
            self._sample_df_curator._update_registry_all(
                validated_only=True, **self._kwargs
            )
        for _, adata_curator in self._mod_adata_curators.items():
            adata_curator._update_registry_all(validated_only=True, **self._kwargs)

    def add_new_from_var_index(self, table: str, organism: str | None = None, **kwargs):
        """Update variable records.

        Args:
            table: The table key.
            organism: The organism name.
            **kwargs: Additional keyword arguments to pass to create new records.
        """
        self._kwargs.update({"organism": organism} if organism else {})
        self._table_adata_curators[table].add_new_from_var_index(
            **self._kwargs, **kwargs
        )

    def add_new_from(
        self,
        key: str,
        accessor: str | None = None,
        organism: str | None = None,
        **kwargs,
    ):
        """Add validated & new categories.

        Args:
            key: The key referencing the slot in the DataFrame.
            accessor: The accessor key such as 'sample' or 'table x'.
            organism: The organism name.
            **kwargs: Additional keyword arguments to pass to create new records.
        """
        if len(kwargs) > 0 and key == "all":
            raise ValueError("Cannot pass additional arguments to 'all' key!")

        self._kwargs.update({"organism": organism} if organism else {})
        if accessor in self._table_adata_curators:
            adata_curator = self._table_adata_curators[accessor]
            adata_curator.add_new_from(key=key, **self._kwargs, **kwargs)
        if accessor == "sample":
            self._sample_df_curator.add_new_from(key=key, **self._kwargs, **kwargs)

    def standardize(self, key: str, accessor: str | None = None):
        """Replace synonyms with standardized values.

        Args:
            key: The key referencing the slot in the `MuData`.
            accessor: The accessor key such as 'sample' or 'table x'.

        Inplace modification of the dataset.
        """
        if accessor in self._table_adata_curators:
            adata_curator = self._table_adata_curators[accessor]
            adata_curator.standardize(key=key)
        if accessor == "sample":
            self._sample_df_curator.standardize(key=key)

    def validate(self, organism: str | None = None) -> bool:
        """Validate variables and categorical observations.

        This method also registers the validated records in the current instance:
        - from public sources
        - from the using_key instance

        Args:
            organism: The organism name.

        Returns:
            Whether the SpatialData object is validated.
        """
        from lamindb.core._settings import settings

        self._kwargs.update({"organism": organism} if organism else {})
        if self._using_key is not None and self._using_key != "default":
            logger.important(
                f"validating using registries of instance {colors.italic(self._using_key)}"
            )

        # add all validated records to the current instance
        verbosity = settings.verbosity
        try:
            settings.verbosity = "error"
            self._update_registry_all()
        finally:
            settings.verbosity = verbosity

        self._non_validated = {}  # type: ignore

        obs_validated = True
        if self._sample_df_curator:
            logger.info('validating categoricals of "sample" metadata...')
            obs_validated &= self._sample_df_curator.validate(**self._kwargs)
            self._non_validated["obs"] = self._sample_df_curator.non_validated  # type: ignore
            logger.print("")

        mods_validated = True
        for table, adata_curator in self._table_adata_curators.items():
            logger.info(f'validating categoricals in table "{table}"...')
            mods_validated &= adata_curator.validate(**self._kwargs)
            if len(adata_curator.non_validated) > 0:
                self._non_validated[table] = adata_curator.non_validated  # type: ignore
            logger.print("")

        self._validated = obs_validated & mods_validated
        return self._validated

    def save_artifact(
        self,
        description: str | None = None,
        key: str | None = None,
        revises: Artifact | None = None,
        run: Run | None = None,
    ) -> Artifact:
        """Save the validated ``MuData`` and metadata.

        Args:
            description: A description of the ``MuData`` object.
            key: A path-like key to reference artifact in default storage, e.g., `"myfolder/myfile.fcs"`.
                Artifacts with the same key form a revision family.
            revises: Previous version of the artifact. Triggers a revision.
            run: The run that creates the artifact.

        Returns:
            A saved artifact record.
        """
        if not self._validated:
            self.validate()
            if not self._validated:
                raise ValidationError("Dataset does not validate. Please curate.")

        verbosity = settings.verbosity
        try:
            settings.verbosity = "warning"

            self._artifact = Artifact(
                self._sdata,
                description=description,
                columns_field=self._var_fields,
                fields=self.categoricals,
                key=key,
                revises=revises,
                run=run,
                **self._kwargs,
            )
            # According to Tim it's not easy to calculate the number of observations.
            # We'd have to write custom code to iterate over labels (which might not even exist at that point)
            self._artifact._accessor = "spatialdata"
            self._artifact.save()

            # Link featuresets
            feature_kwargs = check_registry_organism(
                (list(self._var_fields.values())[0].field.model),
                self._kwargs.get("organism"),
            )

            def _add_set_from_spatialdata(
                host: Artifact | Collection | Run,
                var_fields: dict[str, FieldAttr],
                obs_fields: dict[str, FieldAttr] = None,
                mute: bool = False,
                organism: str | Record | None = None,
            ):
                """Add FeatureSets from SpatialData."""
                if obs_fields is None:
                    obs_fields = {}
                assert host._accessor == "spatialdata"

                sdata = host.load()
                feature_sets = {}

                # sample features
                sample_features = Feature.from_values(self._sample_metadata.columns)
                if len(sample_features) > 0:
                    feature_sets["sample"] = FeatureSet(features=sample_features)

                # table features
                for table, field in var_fields.items():
                    table_fs = parse_feature_sets_from_anndata(
                        sdata[table],
                        var_field=field,
                        obs_field=obs_fields.get(table, Feature.name),
                        mute=mute,
                        organism=organism,
                    )
                    for k, v in table_fs.items():
                        feature_sets[f"['{table}'].{k}"] = v

                def _unify_feature_sets_by_hash(
                    feature_sets: MutableMapping[str, FeatureSet],
                ):
                    unique_values: dict[str, Any] = {}

                    for key, value in feature_sets.items():
                        value_hash = (
                            value.hash
                        )  # Assuming each value has a .hash attribute
                        if value_hash in unique_values:
                            feature_sets[key] = unique_values[value_hash]
                        else:
                            unique_values[value_hash] = value

                    return feature_sets

                # link feature sets
                host._feature_sets = _unify_feature_sets_by_hash(feature_sets)
                host.save()

            _add_set_from_spatialdata(
                self._artifact, var_fields=self._var_fields, **feature_kwargs
            )

            # Link labels
            def _add_labels_from_spatialdata(
                data,
                artifact: Artifact,
                fields: dict[str, FieldAttr],
                feature_ref_is_name: bool | None = None,
            ):
                """Add Labels from SpatialData."""
                features = Feature.lookup().dict()
                for key, field in fields.items():
                    feature = features.get(key)
                    registry = field.field.model
                    filter_kwargs = check_registry_organism(
                        registry, self._kwargs.get("organism")
                    )
                    filter_kwargs_current = get_current_filter_kwargs(
                        registry, filter_kwargs
                    )
                    df = data if isinstance(data, pd.DataFrame) else data.obs
                    labels = registry.from_values(
                        df[key],
                        field=field,
                        **filter_kwargs_current,
                    )
                    if len(labels) == 0:
                        continue
                    label_ref_is_name = None
                    if hasattr(registry, "_name_field"):
                        label_ref_is_name = field.field.name == registry._name_field
                    add_labels(
                        artifact,
                        records=labels,
                        feature=feature,
                        feature_ref_is_name=feature_ref_is_name,
                        label_ref_is_name=label_ref_is_name,
                        from_curator=True,
                    )

            for accessor, accessor_fields in self._categoricals.items():
                column_field = self._var_fields.get(accessor)
                if accessor == "sample":
                    _add_labels_from_spatialdata(
                        self._sample_metadata,
                        self._artifact,
                        accessor_fields,
                        feature_ref_is_name=(
                            None if column_field is None else _ref_is_name(column_field)
                        ),
                    )
                else:
                    _add_labels_from_spatialdata(
                        self._sdata.tables[accessor],
                        self._artifact,
                        accessor_fields,
                        feature_ref_is_name=(
                            None if column_field is None else _ref_is_name(column_field)
                        ),
                    )

        finally:
            settings.verbosity = verbosity

        slug = ln_setup.settings.instance.slug
        if ln_setup.settings.instance.is_remote:  # pragma: no cover
            logger.important(
                f"go to https://lamin.ai/{slug}/artifact/{self._artifact.uid}"
            )

        return self._artifact
