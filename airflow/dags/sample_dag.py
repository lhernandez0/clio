from datetime import timedelta

from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

from airflow import DAG

# Define default_args dictionary
default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    "simple_test_dag",
    default_args=default_args,
    description="A simple test DAG",
    schedule_interval=None,  # Set to None to run manually
    start_date=days_ago(1),  # Start date for the DAG
    catchup=False,  # Do not catch up on past dates
)

# Define a simple BashOperator task
hello_task = BashOperator(
    task_id="print_hello",
    bash_command='echo "Hello, Airflow!"',
    dag=dag,
)

# Set the task sequence (since there's only one task, no need to set dependencies)
