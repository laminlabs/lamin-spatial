import nox
from laminci import upload_docs_artifact
from laminci.nox import build_docs, login_testuser1, run_pre_commit, run_pytest

nox.options.default_venv_backend = "none"


@nox.session
def lint(session: nox.Session) -> None:
    run_pre_commit(session)


@nox.session
def install(session: nox.Session):
    session.run(*"pip install .[dev]".split())
    session.run(
        "pip",
        "install",
        "lamindb[jupyter,bionty,aws,postgres] @"
        " git+https://github.com/laminlabs/lamindb@main",
    )
    session.run(
        "pip",
        "install",
        "--no-deps",
        "lnschema-lamin1 @ git+https://github.com/laminlabs/lnschema-lamin1@main",
    )


@nox.session
def build(session):
    login_testuser1(session)
    run_pytest(session, coverage=False)
    build_docs(session, strip_prefix=True, strict=True)
    upload_docs_artifact(aws=True)
