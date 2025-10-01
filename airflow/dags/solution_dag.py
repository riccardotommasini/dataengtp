import json
import glob
import random
import requests
import pendulum
import pandas as pd
import logging
from datetime import timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

logger = logging.getLogger(__name__)  # Airflow captures this per task
api_url = "https://www.dnd5eapi.co/api" # public D&D 5e API
output_folder = "/opt/airflow/data" # ensure this folder exists and is writable

# --- Failure callback for rich console logs ---
def failure_alert(context):
    exc = context.get("exception")
    ti = context.get("ti")
    logger.error(
        "Task FAILED: dag=%s task=%s run_id=%s try=%s",
        getattr(ti, "dag_id", "?"),
        getattr(ti, "task_id", "?"),
        context.get("run_id"),
        getattr(ti, "try_number", "?"),
    )
    # Full traceback in the task log:
    logger.exception(exc)

# --- DAG config ---
START_DATE = pendulum.datetime(2024, 1, 1, tz="UTC")

with DAG(
    dag_id="solution_dag",
    start_date=START_DATE,
    schedule="0 0 * * *",         # daily at 00:00 UTC
    catchup=False,
    max_active_tasks=1,
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
        "on_failure_callback": failure_alert,
    },
    template_searchpath=["/opt/airflow/data/"],
    tags=["example"],
) as dag:

    # -------- Helpers --------
    def _name_race(output_folder: str, endpoint: str, url: str):
        from faker import Faker
        fake = Faker()
        try:
            logger.info("Fetching races from %s/%s ...", url, endpoint)
            resp = requests.get(f"{url}/{endpoint}", timeout=30)
            resp.raise_for_status()
            races_unfiltered = resp.json()
            races = random.sample([i.get("index") for i in races_unfiltered.get("results", [])], 5)
            rand_names = [fake.first_name() for _ in range(5)]
            payload = {"race": races, "name": rand_names}
            logger.info("Writing first_node.json with %d races and %d names", len(races), len(rand_names))
            with open(f"{output_folder}/first_node.json", "w") as f:
                json.dump(payload, f, ensure_ascii=False)
        except Exception as e:
            logger.exception("Error in _name_race")
            raise

    def _attributes(output_folder: str):
        try:
            attributes = [list(random.randint(6, 19) for _ in range(5)) for _ in range(5)]
            logger.info("Generated attributes matrix shape: 5x5")
            with open(f"{output_folder}/second_node.json", "w") as f:
                json.dump({"attributes": attributes}, f, ensure_ascii=False)
        except Exception:
            logger.exception("Error in _attributes")
            raise

    def _language(output_folder: str, endpoint: str, url: str):
        try:
            logger.info("Fetching languages from %s/%s ...", url, endpoint)
            resp = requests.get(f"{url}/{endpoint}", timeout=30)
            resp.raise_for_status()
            languages_unfiltered = resp.json()
            languages = random.sample([i.get("index") for i in languages_unfiltered.get("results", [])], 5)
            with open(f"{output_folder}/third_node.json", "w") as f:
                json.dump({"language": languages}, f, ensure_ascii=False)
            logger.info("Picked %d languages", len(languages))
        except Exception:
            logger.exception("Error in _language")
            raise

    def _class(output_folder: str, endpoint: str, url: str):
        try:
            logger.info("Fetching classes from %s/%s ...", url, endpoint)
            resp = requests.get(f"{url}/{endpoint}", timeout=30)
            resp.raise_for_status()
            classes_unfiltered = resp.json()
            classes = random.sample([i.get("index") for i in classes_unfiltered.get("results", [])], 5)
            with open(f"{output_folder}/fourth_node.json", "w") as f:
                json.dump({"class": classes}, f, ensure_ascii=False)
            logger.info("Picked classes: %s", classes)
        except Exception:
            logger.exception("Error in _class")
            raise

    def _proficiency_choices(output_folder: str, url: str):
        try:
            with open(f"{output_folder}/fourth_node.json", "r") as read_file:
                load_classes = json.load(read_file)
            classes = load_classes.get("class", [])
            logger.info("Computing proficiencies for %d classes", len(classes))

            def get_proficiencies(cls):
                d = requests.get(f"{url}/classes/{cls}", timeout=30).json()
                first_choice = (d.get("proficiency_choices") or [{}])[0]
                options = (first_choice.get("from").get("options") or [])   # <-- fixed name
                choose_n = int(first_choice.get("choose") or 0)
                picked = random.sample([i.get("item").get("index") for i in options], choose_n) if choose_n and options else []
                logger.debug("class=%s choose=%s -> %s", cls, choose_n, picked)
                return picked
    
            final_list = [get_proficiencies(c) for c in classes]
            with open(f"{output_folder}/fifth_node.json", "w") as f:
                json.dump({"proficiences": final_list}, f, ensure_ascii=False)
            logger.info("Wrote proficiencies for %d classes", len(final_list))
        except Exception:
            logger.exception("Error in _proficiency_choices")
            raise

    def _levels(output_folder: str):
        try:
            random_levels = [random.randint(1, 3) for _ in range(5)]
            with open(f"{output_folder}/sixth_node.json", "w") as f:
                json.dump({"levels": random_levels}, f, ensure_ascii=False)
            logger.info("Generated levels: %s", random_levels)
        except Exception:
            logger.exception("Error in _levels")
            raise

    def _spell_check(output_folder: str, url: str):
        try:
            with open(f"{output_folder}/fourth_node.json", "r") as read_file:
                load_classes = json.load(read_file)
            classes = load_classes.get("class", [])
            logger.info("Checking spell counts for %d classes", len(classes))

            def spellcount(cls):
                resp = requests.get(f"{url}/classes/{cls}/spells", timeout=30).json()
                return int(resp.get("count") or 0)

            total = sum(spellcount(c) for c in classes)
            logger.info("Total spell count across classes: %d", total)
            return "spells" if total > 0 else "merge"
        except Exception:
            logger.exception("Error in _spell_check")
            raise

    def _spells(output_folder: str, url: str):
        try:
            with open(f"{output_folder}/fourth_node.json", "r") as read_file:
                load_classes = json.load(read_file)
            classes = load_classes.get("class", [])
            logger.info("Fetching spells for %d classes", len(classes))

            def get_spells(cls):
                resp = requests.get(f"{url}/classes/{cls}/spells", timeout=30).json()
                results = resp.get("results", [])
                pick = random.randint(1, min(3, len(results))) if results else 0
                chosen = random.sample([i.get("index") for i in results], pick) if pick else []
                logger.debug("Class=%s picked %d spells -> %s", cls, pick, chosen)
                return chosen

            spell_lists = [get_spells(c) for c in classes]
            with open(f"{output_folder}/seventh_node.json", "w") as f:
                json.dump({"spells": spell_lists}, f, ensure_ascii=False)
            logger.info("Wrote spells list")
        except Exception:
            logger.exception("Error in _spells")
            raise

    def _merge(output_folder: str):
        try:
            jsons = sorted(glob.glob(f"{output_folder}/*_node.json"))
            logger.info("Merging %d JSON node files", len(jsons))
            dfs = [pd.read_json(p) for p in jsons]
            df = pd.concat(dfs, axis=1) if dfs else pd.DataFrame()
            df.to_csv(f"{output_folder}/eight_node.csv", index=False)
            logger.info("Wrote %s/eight_node.csv with %d rows, %d cols", output_folder, *df.shape if not df.empty else (0, 0))
        except Exception:
            logger.exception("Error in _merge")
            raise

    def _insert(output_folder: str):
        try:
            df = pd.read_csv(f"{output_folder}/eight_node.csv")
            logger.info("Generating inserts from CSV shape=%s", df.shape)
            with open(f"{output_folder}/inserts.sql", "w") as f:
                f.write(
                    "CREATE TABLE IF NOT EXISTS characters (\n"
                    "  race TEXT,\n"
                    "  name TEXT,\n"
                    "  proficiences TEXT,\n"
                    "  language TEXT,\n"
                    "  spells TEXT,\n"
                    "  class TEXT,\n"
                    "  levels TEXT,\n"
                    "  attributes TEXT\n"
                    ");\n"
                )
                for _, row in df.iterrows():
                    race = row.get("race", "")
                    name = row.get("name", "")
                    proficiences = row.get("proficiences", "")
                    language = row.get("language", "")
                    spells = row.get("spells", "")
                    class_ = row.get("class", "")
                    levels = row.get("levels", "")
                    attributes = row.get("attributes", "")
                    f.write(
                        "INSERT INTO characters VALUES ("
                        f"'{race}', '{name}', $${proficiences}$$, '{language}', $${spells}$$, '{class_}', '{levels}', $${attributes}$$"
                        ");\n"
                    )

            logger.info("Wrote SQL file: %s/inserts.sql", output_folder)
        except Exception:
            logger.exception("Error in _insert")
            raise

    # -------- Tasks --------
    first_node = PythonOperator(
        task_id="name_race",
        python_callable=_name_race,
        op_kwargs={"output_folder": output_folder, "endpoint": "races", "url": api_url},
    )

    second_node = PythonOperator(
        task_id="attributes",
        python_callable=_attributes,
        op_kwargs={"output_folder": output_folder},
    )

    third_node = PythonOperator(
        task_id="language",
        python_callable=_language,
        op_kwargs={"output_folder": output_folder, "endpoint": "languages", "url": api_url},
    )

    fourth_node = PythonOperator(
        task_id="class",
        python_callable=_class,
        op_kwargs={"output_folder": output_folder, "endpoint": "classes", "url": api_url},
    )

    fifth_node = PythonOperator(
        task_id="proficiency_choices",
        python_callable=_proficiency_choices,
        op_kwargs={"output_folder": output_folder, "url": api_url},
    )

    sixth_node = PythonOperator(
        task_id="levels",
        python_callable=_levels,
        op_kwargs={"output_folder": output_folder},
    )

    seventh_node = BranchPythonOperator(
        task_id="spell_check",
        python_callable=_spell_check,
        op_kwargs={"output_folder": output_folder, "url": api_url},
    )

    seventh_node_a = PythonOperator(
        task_id="spells",
        python_callable=_spells,
        op_kwargs={"output_folder": output_folder, "url": api_url},
    )

    eight_node = PythonOperator(
        task_id="merge",
        python_callable=_merge,
        op_kwargs={"output_folder": output_folder},
    )

    ninth_node = PythonOperator(
        task_id="generate_insert",
        python_callable=_insert,
        op_kwargs={"output_folder": output_folder},
    )

    tenth_node = SQLExecuteQueryOperator(
        task_id="insert_inserts",
        conn_id="postgres_default",
        sql="inserts.sql",
        autocommit=True,
    )

    eleventh_node = EmptyOperator(task_id="finale")

    # -------- Graph --------
    [first_node, second_node, third_node, fourth_node] >> fifth_node
    fifth_node >> sixth_node >> seventh_node >> [seventh_node_a, eight_node]
    seventh_node_a >> eight_node >> ninth_node >> tenth_node >> eleventh_node
