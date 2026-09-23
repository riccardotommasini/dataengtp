import pendulum
from datetime import timedelta
import urllib.request as request
import pandas as pd

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

START_DATE = pendulum.datetime(2020, 6, 25, tz="UTC")
prev_ep = "1588612377" #"{{ prev_data_interval_start_success.int_timestamp if prev_data_interval_start_success else data_interval_start.int_timestamp }}"

with DAG(
    dag_id="second_dag",
    start_date=START_DATE,
    schedule="0 0 * * *",          # daily at 00:00 UTC
    catchup=False,
    max_active_tasks=1,
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    template_searchpath=["/opt/airflow/data/"],  # for SQL files
    tags=["example"],
) as dag:

    # --- Helpers ---
    def _get_spreadsheet(epoch: str, url: str, output_folder: str):
        request.urlretrieve(url=url, filename=f"{output_folder}/{epoch}.xlsx")

    def _time_filter(previous_epoch: str, epoch: str, next_epoch: str, output_folder: str):
        df = pd.read_csv(f"{output_folder}/{epoch}_correct.csv")
        prev_i = int(previous_epoch)
        next_i = int(next_epoch)
        df_filtered = df[(df["Modified"] >= prev_i) & (df["Modified"] <= next_i)]
        df_filtered.to_csv(f"{output_folder}/{previous_epoch}_filtered.csv", index=False)

    def _emptiness_check(previous_epoch: str, output_folder: str):
        df = pd.read_csv(f"{output_folder}/{previous_epoch}_filtered.csv")
        return "end" if df.empty else "split"

    def _split(previous_epoch: str, output_folder: str):
        df = pd.read_csv(f"{output_folder}/{previous_epoch}_filtered.csv")
        df = df.replace(',|"|\'|`', "", regex=True)
        df_intavolature = df[["Piece", "Type", "Key", "Difficulty", "Date", "Ensemble"]]
        df_composer = df[["Composer"]].drop_duplicates()
        df_intavolature.to_csv(f"{output_folder}/{previous_epoch}_intavolature.csv", index=False)
        df_composer.to_csv(f"{output_folder}/{previous_epoch}_composer.csv", index=False)

    def _create_intavolature_query(previous_epoch: str, output_folder: str):
        df = pd.read_csv(f"{output_folder}/{previous_epoch}_intavolature.csv")
        with open("/opt/airflow/data/intavolature_inserts.sql", "w") as f:
            f.write(
                "CREATE TABLE IF NOT EXISTS intavolature (\n"
                "  title VARCHAR(255),\n"
                "  subtitle VARCHAR(255),\n"
                "  key VARCHAR(255),\n"
                "  difficulty VARCHAR(255),\n"
                "  date VARCHAR(255),\n"
                "  ensemble VARCHAR(255)\n"
                ");\n"
            )
            for _, row in df.iterrows():
                piece = row.get("Piece", "")
                type_ = row.get("Type", "")
                key = row.get("Key", "")
                difficulty = row.get("Difficulty", "")
                date = row.get("Date", "")
                ensemble = row.get("Ensemble", "")
                f.write(
                    "INSERT INTO intavolature VALUES ("
                    f"'{piece}', '{type_}', '{key}', '{difficulty}', '{date}', '{ensemble}'"
                    ");\n"
                )

    def _create_composer_query(previous_epoch: str, output_folder: str):
        df = pd.read_csv(f"{output_folder}/{previous_epoch}_composer.csv")
        with open("/opt/airflow/data/composer_inserts.sql", "w") as f:
            f.write(
                "CREATE TABLE IF NOT EXISTS composer (\n"
                "  name VARCHAR(255)\n"
                ");\n"
            )
            for _, row in df.iterrows():
                composer = row.get("Composer", "")
                f.write(f"INSERT INTO composer VALUES ('{composer}');\n")

    # --- Tasks ---
    get_spreadsheet = PythonOperator(
        task_id="get_spreadsheet",
        python_callable=_get_spreadsheet,
        op_kwargs={
            "output_folder": "/opt/airflow/data",
            "epoch": "{{ data_interval_start.int_timestamp }}",
            "url": "https://www.lutemusic.org/spreadsheet.xlsx",
        },
    )
    
    transmute_to_csv = BashOperator(
        task_id="transmute_to_csv",
        bash_command=(
            "xlsx2csv /opt/airflow/data/{{ data_interval_start.int_timestamp }}.xlsx "
            "> /opt/airflow/data/{{ data_interval_start.int_timestamp }}_correct.csv"
        ),
    )

    time_filter = PythonOperator(
        task_id="time_filter",
        python_callable=_time_filter,
        op_kwargs={
            "output_folder": "/opt/airflow/data",
            "epoch": "{{ data_interval_start.int_timestamp }}",
            "previous_epoch": prev_ep,
            "next_epoch": "{{ data_interval_end.int_timestamp }}",
        },
    )

    emptiness_check = BranchPythonOperator(
        task_id="emptiness_check",
        python_callable=_emptiness_check,
        op_kwargs={
            "previous_epoch": prev_ep,
            "output_folder": "/opt/airflow/data",
        },
    )

    split = PythonOperator(
        task_id="split",
        python_callable=_split,
        op_kwargs={
            "output_folder": "/opt/airflow/data",
            "previous_epoch": prev_ep,
        },
    )

    create_intavolature_query = PythonOperator(
        task_id="create_intavolature_query",
        python_callable=_create_intavolature_query,
        op_kwargs={
            "previous_epoch": prev_ep,
            "output_folder": "/opt/airflow/data",
        },
    )

    create_composer_query = PythonOperator(
        task_id="create_composer_query",
        python_callable=_create_composer_query,
        op_kwargs={
            "previous_epoch": prev_ep,
            "output_folder": "/opt/airflow/data",
        },
    )

    insert_intavolature_query = SQLExecuteQueryOperator(
        task_id="insert_intavolature_query",
        conn_id="postgres_default",   # same connection as before; change if needed
        sql="intavolature_inserts.sql",
        autocommit=True,
    )

    insert_composer_query = SQLExecuteQueryOperator(
        task_id="insert_composer_query",
        conn_id="postgres_default",
        sql="composer_inserts.sql",
        autocommit=True,
    )

    join_tasks = EmptyOperator(
        task_id="coalesce_transformations",
        trigger_rule="none_failed",
    )

    end = EmptyOperator(
        task_id="end",
        trigger_rule="none_failed",
    )

    # --- Graph ---
    get_spreadsheet >> transmute_to_csv >> time_filter >> emptiness_check
    emptiness_check >> [split, end]
    split >> [create_intavolature_query, create_composer_query]
    create_intavolature_query >> insert_intavolature_query
    create_composer_query >> insert_composer_query
    [insert_intavolature_query, insert_composer_query] >> join_tasks >> end
