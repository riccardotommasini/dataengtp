import pendulum
from datetime import timedelta

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.bash import BashOperator

START_DATE = pendulum.datetime(2024, 1, 1, tz="UTC")

with DAG(
    dag_id="first_dag_stub",
    start_date=START_DATE,
    schedule=None,          # no schedule
    catchup=False,
    max_active_tasks=1,     # old 'concurrency'
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["stub"],
) as dag:

    get_spreadsheet = BashOperator(task_id="get_spreadsheet", bash_command="curl https://lutemusic.org/spreadsheet.xlsx --output /opt/airflow/data/{{ds_nodash}}.xlsx")
    transmute_to_csv = BashOperator(task_id="transmute_to_csv",bash_command="xlsx2csv /opt/airflow/data/{{ds_nodash}}.xlsx > /opt/airflow/data/{{ds_nodash}}_correct.csv")
    time_filter = BashOperator(task_id="time_filter", bash_command="awk -F, 'int($31) > 1588612377' /opt/airflow/data/{{ds_nodash}}_correct.csv > /opt/airflow/data/{{ds_nodash}}_correct_filtered.csv")
    load = BashOperator(task_id="load", bash_command="echo \"loaded\"")
    cleanup = BashOperator(task_id="cleanup", bash_command="rm /opt/airflow/data/{{ds_nodash}}*")

    get_spreadsheet >> transmute_to_csv >> time_filter >> load >> cleanup
