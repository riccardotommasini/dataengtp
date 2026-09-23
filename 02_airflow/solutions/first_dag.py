import pendulum
from datetime import timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

# Recommended: set a static start date (no "today"-like functions)
START_DATE = pendulum.datetime(2024, 1, 1, tz="UTC")

with DAG(
    dag_id="first_dag",
    start_date=START_DATE,
    schedule=None,            # replaces schedule_interval=None
    catchup=False,
    max_active_tasks=1,       # replaces old DAG-level 'concurrency'
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["example"],
) as dag:

    # 1) Download the spreadsheet
    get_spreadsheet = BashOperator(
        task_id="get_spreadsheet",
        bash_command=(
            "curl -fsSL https://www.lutemusic.org/spreadsheet.xlsx "
            "--output /opt/airflow/data/{{ ds_nodash }}.xlsx"
        ),
    )

    # 2) Convert xlsx → csv
    transmute_to_csv = BashOperator(
        task_id="transmute_to_csv",
        bash_command=(
            "xlsx2csv /opt/airflow/data/{{ ds_nodash }}.xlsx "
            "> /opt/airflow/data/{{ ds_nodash }}_correct.csv"
        ),
    )

    # 3) Filter rows (31st column as epoch seconds)
    time_filter = BashOperator(
        task_id="time_filter",
        bash_command=(
            "awk -F, 'int($31) > 1588612377' "
            "/opt/airflow/data/{{ ds_nodash }}_correct.csv "
            "> /opt/airflow/data/{{ ds_nodash }}_correct_filtered.csv"
        ),
    )

    # 4) Load step (placeholder)
    load = BashOperator(
        task_id="load",
        bash_command='echo "done"',
    )

    # 5) Cleanup intermediates
    cleanup = BashOperator(
        task_id="cleanup",
        bash_command=(
            "rm -f "
            "/opt/airflow/data/{{ ds_nodash }}_correct.csv "
            # "/opt/airflow/dags/{{ ds_nodash }}_correct_filtered.csv "
            "/opt/airflow/data/{{ ds_nodash }}.xlsx"
        ),
        trigger_rule="all_done",  # ensure cleanup even if an upstream task fails
    )

    get_spreadsheet >> transmute_to_csv >> time_filter >> load >> cleanup
