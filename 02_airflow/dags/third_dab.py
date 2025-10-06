import pendulum
from datetime import timedelta
import logging
from faker import Faker
import random
import json
import requests

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator, BranchPythonOperator
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
# from airflow.providers.postgres.operators.postgres import PostgresOperator

START_DATE = pendulum.datetime(2025, 1, 1, tz="UTC")
BASE_API_URL = "https://www.dnd5eapi.co/api/2014"
DEFAULT_TIMEOUT = 10
DEFAULT_OUTPUT_FOLDER = "/opt/airflow/data"
NB_PLAYERS = 5

fake = Faker()
logger = logging.getLogger(__name__)

with DAG(
    dag_id="third_dag",
    start_date=START_DATE,
    schedule="0 20 * * 5",
    catchup=False,
    max_active_tasks=1,       # replaces old DAG-level 'concurrency'
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    template_searchpath=["/opt/airflow/data/"],  # for SQL files
    tags=["example"],
) as dag:

    def _pick_races(url: str, output_folder: str, timeout=DEFAULT_TIMEOUT):
        r = requests.get(f"{url}/races", timeout=timeout)
        races = json.loads(r.text)["results"]

        players_races = []
        for _ in range(NB_PLAYERS):
            player_race = random.choice(races)["index"]
            players_races.append(player_race)

        with open(f"{output_folder}/races.json", 'w') as file:
            json.dump(players_races, file)
        logger.debug(f"Players races written to file.")

    def _get_languages(url: str, output_folder: str, timeout=DEFAULT_TIMEOUT):
        with open(f"{output_folder}/races.json", 'r') as file:
            players_races = json.load(file)

        players_languages = []
        for race in players_races:
            r = requests.get(f"{url}/races/{race}", timeout=timeout)
            languages = [language["name"] for language in json.loads(r.text)["languages"]]
            players_languages.append(languages)

        with open(f"{output_folder}/languages.json", 'w') as file:
            json.dump(players_languages, file)
        logger.debug(f"Players languages written to file.")

    def _generate_attributes(output_folder: str):
        players_attributes = []
        
        for _ in range(NB_PLAYERS):
            _strength = random.randint(6,18)
            _dexterity = random.randint(2,18)
            _constitution = random.randint(2,18)
            _intelligence = random.randint(2,18)
            _wisdom = random.randint(2,18)
            _charisma = random.randint(2,18)
            player_attributes = [_strength,_dexterity,_constitution,_intelligence,_wisdom,_charisma]
            # player_attributes = f"[{_strength},{_dexterity},{_constitution},{_intelligence},{_wisdom},{_charisma}]"
            players_attributes.append(player_attributes)

        with open(f"{output_folder}/attributes.json", 'w') as file:
            json.dump(players_attributes, file)
        logger.debug(f"Players attributes written to file.")

    def _pick_classes(url: str, output_folder: str, timeout=DEFAULT_TIMEOUT):
        r = requests.get(f"{url}/classes", timeout=timeout)
        classes = json.loads(r.text)["results"]

        players_classes = []
        for _ in range(NB_PLAYERS):
            player_class = random.choice(classes)["index"]
            players_classes.append(player_class)

        with open(f"{output_folder}/classes.json", 'w') as file:
            json.dump(players_classes, file)
        logger.debug(f"Players classes written to file.")

    def _pick_proficiencies(url: str, output_folder: str, timeout=DEFAULT_TIMEOUT):
        with open(f"{output_folder}/classes.json", 'r') as file:
            players_classes = json.load(file)

        players_proficiencies = []
        for pclass in players_classes:
            r = requests.get(f"{url}/classes/{pclass}", timeout=timeout)
            proficiency_choices = json.loads(r.text)["proficiency_choices"][0]
            nb_proficiency_choice = proficiency_choices["choose"]
            class_proficiencies = proficiency_choices["from"]["options"]

            player_proficiencies = []
            for _ in range(nb_proficiency_choice):
                proficiency = random.choice(class_proficiencies)
                proficiency_name = proficiency["item"]["name"]
                class_proficiencies.remove(proficiency)
                player_proficiencies.append(proficiency_name)
            players_proficiencies.append(player_proficiencies)

        with open(f"{output_folder}/proficiencies.json", 'w') as file:
            json.dump(players_proficiencies, file)
        logger.debug(f"Players proficiencies written to file.")

    def _generate_names_and_levels(output_folder: str):
        players_names_levels = []
        
        for _ in range(NB_PLAYERS):
            _name = fake.name()
            _level = random.randint(1,4)
            player_name_level = {"name": _name, "level": _level}
            players_names_levels.append(player_name_level)

        with open(f"{output_folder}/names_levels.json", 'w') as file:
            json.dump(players_names_levels, file)
        logger.debug(f"Players names and levels written to file.")

    def _pick_spells(url: str, output_folder: str, timeout=DEFAULT_TIMEOUT):
        with open(f"{output_folder}/classes.json", 'r') as file:
            players_classes = json.load(file)
        with open(f"{output_folder}/names_levels.json", 'r') as file:
            players_names_levels = json.load(file)

        players_levels = [player["level"] for player in players_names_levels]

        players_spells = []
        for (pclass, level) in zip(players_classes, players_levels):
            r = requests.get(f"{url}/classes/{pclass}/spells", timeout=timeout)
            json_response = json.loads(r.text)
            class_spells = json_response["results"]
            class_spells_under_level3 = [spell["index"] for spell in class_spells if spell["level"] < 3]
            nb_class_spells = json_response["count"]

            player_spells = []
            for _ in range(min(level+3, len(class_spells_under_level3))):
                random_spell = random.choice(class_spells_under_level3)
                player_spells.append(random_spell)
                class_spells_under_level3.remove(random_spell)
            players_spells.append(player_spells)

        with open(f"{output_folder}/spells.json", 'w') as file:
            json.dump(players_spells, file)
        logger.debug(f"Players spells written to file.")


    def _create_table_query(output_folder: str):
        with open("/opt/airflow/data/create_table.sql", "w") as f:
            f.write("""CREATE TABLE IF NOT EXISTS dnd (name VARCHAR(255), level VARCHAR(255), race VARCHAR(255), class VARCHAR(255), spells VARCHAR(255), languages VARCHAR(255), profficiencies VARCHAR(255), attributes VARCHAR(255));\n"""
            )

    def _create_data_query(output_folder: str):
        with open(f"{output_folder}/names_levels.json", 'r') as file:
            names_levels = json.load(file)
        with open(f"{output_folder}/races.json", 'r') as file:
            races = json.load(file)
        with open(f"{output_folder}/classes.json", 'r') as file:
            classes = json.load(file)
        with open(f"{output_folder}/spells.json", 'r') as file:
            spells = json.load(file)
        with open(f"{output_folder}/languages.json", 'r') as file:
            languages = json.load(file)
        with open(f"{output_folder}/proficiencies.json", 'r') as file:
            proficiencies = json.load(file)
        with open(f"{output_folder}/attributes.json", 'r') as file:
            attributes = json.load(file)

        with open("/opt/airflow/data/data_inserts.sql", "w") as f:
            for (pname_level, prace, pclass, pspells, planguages, pproficiencies, pattributes) in zip(names_levels, races, classes, spells, languages, proficiencies, attributes):
                pname = pname_level['name']
                plevel = pname_level['level']
                player = f"""
                    INSERT INTO dnd VALUES 
                    ('{pname}',
                     '{plevel}',
                     '{prace}',
                     '{pclass}',
                     $${pspells}$$,
                     $${planguages}$$,
                     $${pproficiencies}$$,
                     $${pattributes}$$
                    );\n"""
                f.write(player)

    pick_races = PythonOperator(
        task_id="pick_races",
        python_callable=_pick_races,
        op_kwargs={
            "url": BASE_API_URL,
            "output_folder": DEFAULT_OUTPUT_FOLDER
        },
    )

    get_languages = PythonOperator(
        task_id="get_languages",
        python_callable=_get_languages,
        op_kwargs={
            "url": BASE_API_URL,
            "output_folder": DEFAULT_OUTPUT_FOLDER
        },
    )

    generate_attributes = PythonOperator(
        task_id="generate_attributes",
        python_callable=_generate_attributes,
        op_kwargs={
            "output_folder": DEFAULT_OUTPUT_FOLDER
        },
    )

    pick_classes = PythonOperator(
        task_id="pick_classes",
        python_callable=_pick_classes,
        op_kwargs={
            "url": BASE_API_URL,
            "output_folder": DEFAULT_OUTPUT_FOLDER
        },
    )

    pick_proficiencies = PythonOperator(
        task_id="pick_proficiencies",
        python_callable=_pick_proficiencies,
        op_kwargs={
            "url": BASE_API_URL,
            "output_folder": DEFAULT_OUTPUT_FOLDER
        },
    )

    generate_names_and_levels = PythonOperator(
        task_id="generate_names_and_levels",
        python_callable=_generate_names_and_levels,
        op_kwargs={
            "output_folder": DEFAULT_OUTPUT_FOLDER
        },
    )

    pick_spells = PythonOperator(
        task_id="pick_spells",
        python_callable=_pick_spells,
        op_kwargs={
            "url": BASE_API_URL,
            "output_folder": DEFAULT_OUTPUT_FOLDER
        },
    )

    join_tasks = EmptyOperator(
        task_id="join_tasks",
        trigger_rule="none_failed",
    )

    create_table_query = PythonOperator(
        task_id="create_table_query",
        python_callable=_create_table_query,
        op_kwargs={
            "output_folder": DEFAULT_OUTPUT_FOLDER
        },
    )

    create_table = SQLExecuteQueryOperator(
        task_id="create_table",
        conn_id="postgres_not_default",
        sql="create_table.sql",
        autocommit=True,
    )

    create_data_query = PythonOperator(
        task_id="create_data_query",
        python_callable=_create_data_query,
        op_kwargs={
            "output_folder": DEFAULT_OUTPUT_FOLDER
        },
    )

    insert_data = SQLExecuteQueryOperator(
        task_id="insert_data",
        conn_id="postgres_not_default",
        sql="data_inserts.sql",
        autocommit=True,
    )

    end = EmptyOperator(
        task_id="end",
        trigger_rule="none_failed",
    )

    pick_races >> get_languages
    pick_classes >> pick_proficiencies
    [generate_names_and_levels, pick_classes] >> pick_spells
    [generate_attributes, pick_proficiencies, pick_spells, get_languages] >> join_tasks
    join_tasks >> [create_table_query, create_data_query]
    create_table_query >> create_table
    [create_table, create_data_query] >> insert_data >> end
