import nox
from laminci import upload_docs_artifact
from laminci.nox import build_docs, run_pre_commit

nox.options.default_venv_backend = "none"


@nox.session
def lint(session: nox.Session) -> None:
    run_pre_commit(session)


@nox.session
def build(session):
    session.run(
        "uv",
        "pip",
        "install",
        "--system",
        "lamindb_setup @ git+https://github.com/laminlabs/lamindb_setup@gcp",
    )
    session.run(
        "uv",
        "pip",
        "install",
        "--system",
        "lamindb @ git+https://github.com/laminlabs/lamindb@spatial",
    )
    session.run(*"uv pip install --system -r requirements.txt".split())
    session.run(*"pytest -s tests".split())
    build_docs(session, strict=True)
    upload_docs_artifact(aws=True)
