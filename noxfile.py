import nox
from laminci import upload_docs_artifact
from laminci.nox import (
    SYSTEM,
    build_docs,
    install_lamindb,
    login_testuser1,
    run,
    run_pre_commit,
)

nox.options.default_venv_backend = "none"


@nox.session
def lint(session: nox.Session) -> None:
    run_pre_commit(session)


@nox.session
def build(session):
    # do not use zarr extra here otherwise spatialdata won't be installed
    install_lamindb(session, branch="main", extras="bionty,gcp,jupyter,zarr")
    run(session, f"uv pip install {SYSTEM} .[dev,use_case]")
    run(session, f"uv pip install {SYSTEM} spatialdata<=0.5.0")
    login_testuser1(session)
    run(session, "pytest -s tests")
    build_docs(session, strict=True)
    upload_docs_artifact(aws=True)
