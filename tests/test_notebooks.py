from pathlib import Path

import nbproject_test as test


def test_overview():
    Path(__file__).parents[1] / "docs/"
    # test.execute_notebooks(docs_folder, write=True)


def test_notebooks():
    Path(__file__).parents[1] / "docs/notebooks/"
    # test.execute_notebooks(docs_folder, write=True)
