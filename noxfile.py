import nox
from laminci import upload_docs_artifact
from laminci.nox import build_docs, install_lamindb, login_testuser1, run_pre_commit

nox.options.default_venv_backend = "none"


@nox.session
def lint(session: nox.Session) -> None:
    run_pre_commit(session)


@nox.session
def build(session):
    install_lamindb(session, branch="release", extras="bionty,aws,jupyter")
    session.run(*"uv pip install --system wetlab findrefs vitessce starlette".split())
    login_testuser1(session)
    session.run(*"pytest -s tests".split())
    build_docs(session, strict=True)
    upload_docs_artifact(aws=True)
