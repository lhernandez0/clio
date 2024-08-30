from airflow.models import DagBag


def test_dag_integrity():
    dag_bag = DagBag(include_examples=False)
    assert not dag_bag.import_errors, "DAG import errors found!"
