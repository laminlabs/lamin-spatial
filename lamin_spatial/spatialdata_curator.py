from typing import Iterable

import pandas as pd
from lamindb._curate import AnnDataCurator, CurateLookup, DataFrameCurator
from lamindb.core.exceptions import ValidationError
from lnschema_core import Artifact, Feature, Record, Run
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
        self._obs_fields = self._parse_categoricals(categoricals)
        self._tables = set(self._var_fields.keys()) | set(self._obs_fields.keys())
        self._using_key = using_key
        self._verbosity = verbosity
        self._obs_df_curator = None
        self._sample_metadata = self._sdata.get_attrs(
            key="spatialdata-db", return_as="df", flatten=False
        )  # this key will need to be adapted in the future

        if "obs" in self._tables:
            self._obs_df_curator = DataFrameCurator(
                df=self._sample_metadata,
                columns=Feature.name,
                categoricals=self._obs_fields.get("obs", {}),
                using_key=using_key,
                verbosity=verbosity,
                sources=self._sources.get("obs"),
                exclude=self._exclude.get("obs"),
                check_valid_keys=False,
                **self._kwargs,
            )
        self._table_adata_curators = {
            table: AnnDataCurator(
                data=sdata[table],
                var_index=var_index.get(table),
                categoricals=self._obs_fields.get(table),
                using_key=using_key,
                verbosity=verbosity,
                sources=self._sources.get(table),
                exclude=self._exclude.get(table),
                **self._kwargs,
            )
            for table in self._tables
            if table != "obs"
        }
        self._non_validated = None

    @property
    def var_index(self) -> FieldAttr:
        """Return the registry field to validate variables index against."""
        return self._var_fields

    @property
    def categoricals(self) -> dict:
        """Return the obs fields to validate against."""
        return self._obs_fields

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

    def _parse_categoricals(self, categoricals: dict[str, FieldAttr]) -> dict:
        """Parse the categorical fields."""
        pass

    def lookup(
        self, using_key: str | None = None, public: bool = False
    ) -> CurateLookup:
        """Lookup categories.

        Args:
            using_key: The instance where the lookup is performed.
                if "public", the lookup is performed on the public reference.
        """
        pass

    def _replace_synonyms(
        self, key: str, syn_mapper: dict, values: pd.Series | pd.Index
    ):
        pass

    def _update_registry_all(self):
        """Update all registries."""
        pass

    def add_new_from(
        self,
        key: str,
        modality: str | None = None,
        organism: str | None = None,
        **kwargs,
    ):
        pass

    def standardize(self, key: str) -> None:
        """Replace synonyms with standardized values.

        Modifies the input dataset inplace.

        Args:
            key: The key referencing the column in the DataFrame to standardize.
        """
        pass

    def validate(self, organism: str | None = None) -> bool:
        """Validate variables and categorical observations.

        This method also registers the validated records in the current instance:
        - from public sources
        - from the using_key instance

        Args:
            organism: The organism name.

        Returns:
            Whether the DataFrame is validated.
        """

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
