import pytest


@pytest.fixture(autouse=True, scope="session")
def reset_db():
    from airflow.utils import db

    db.resetdb()
    yield
