import nox
from laminci import upload_docs_artifact
from laminci.nox import build_docs, login_testuser1, run_pre_commit

nox.options.default_venv_backend = "none"


@nox.session
def lint(session: nox.Session) -> None:
    run_pre_commit(session)


@nox.session()
def build(session):
    session.run(*"pip install -r requirements.txt".split())
    session.run(
        "pip",
        "install",
        "lamindb @ git+https://github.com/laminlabs/lamindb@main",
    )
    login_testuser1(session)
    session.run(*"pytest -s tests".split())
    build_docs(session, strict=True)
    upload_docs_artifact(aws=True)
