import pendulum
from datetime import timedelta
import urllib.request as request
import pandas as pd

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

import requests, logging, random, os, csv

START_DATE = pendulum.datetime(2020, 6, 25, tz="UTC")
prev_ep = "1588612377" #"{{ prev_data_interval_start_success.int_timestamp if prev_data_interval_start_success else data_interval_start.int_timestamp }}"

# name_race → attributes → language → class → proficiency_choices 
# → levels → spell_check → (spells?) → merge → generate_sql → insert_inserts → finale

with DAG(
    dag_id="dnd",
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
    def _log_info(message):
        logging.info("------------- ", message)

    def _random_name():
        url = "https://randomuser.me/api/"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            _log_info("API call succeeded.")
            name = data["results"][0]["name"]
            full_name = f'{name["first"]} {name["last"]}'
            _log_info(f"Name : {full_name}") 
            return full_name  
        else:
            _log_info(f"API call failed with status {response.status_code}")

    def _random_race():
        _log_info("Random race")
        url = "https://www.dnd5eapi.co/api/2014/races/"
        response = requests.get(url)
        data = response.json()

        count = data["count"]
        race_index = data["results"][random.randint(0,count-1)]["index"]

        _log_info("Race :" + race_index)
        return race_index
    
    def _random_attributes():
        _log_info("Random attributes")

        strength = random.randint(6,18)
        dexterity = random.randint(2,18)
        constitution = random.randint(2,18)
        intelligence = random.randint(2,18)
        wisdom = random.randint(2,18)
        charisma = random.randint(2,18)
        _log_info("Attributes " + str([strength, dexterity, constitution, intelligence, wisdom, charisma]))
        return [strength, dexterity, constitution, intelligence, wisdom, charisma]
    
    def _languages_from_race(ti):
        _log_info("Languages from race")
        race = ti.xcom_pull(task_ids="random_race")  

        url = "https://www.dnd5eapi.co/api/2014/races/" + race
        response = requests.get(url)
        data = response.json()

        languages = data["languages"]
        languages_list = []

        for lan in languages:
            languages_list.append(lan["index"])

        return languages_list
    
    def _random_class():
        _log_info("Random class")
        url = "https://www.dnd5eapi.co/api/2014/classes/"
        response = requests.get(url)
        data = response.json()

        count = data["count"]
        class_index = data["results"][random.randint(0,count-1)]["index"]

        _log_info("Class :" + class_index)
        return class_index

    def _proficiency_choices_from_class(ti):
        _log_info("Proficiency choices from class")
        class_index = ti.xcom_pull(task_ids="random_class")  

        url = "https://www.dnd5eapi.co/api/2014/classes/" + class_index
        response = requests.get(url)
        data = response.json()

        proficiency_choices = data["proficiency_choices"][0]
        number_choices = proficiency_choices["choose"]
        proficiency_list = []

        for pro in proficiency_choices["from"]["options"]:
            proficiency_list.append(pro["item"]["index"])

        proficiency_chosen = []
        for i in range(number_choices):
            choice = proficiency_list[random.randint(0,len(proficiency_list))]
            proficiency_chosen.append(choice)
            proficiency_list.remove(choice)

        return proficiency_chosen
    
    def _add_character_in_csv(ti, csv_file="/opt/airflow/data/characters.csv"):
        # Pull values from previous tasks
        name = ti.xcom_pull(task_ids="random_name")
        attributes = ti.xcom_pull(task_ids="random_attributes")
        race = ti.xcom_pull(task_ids="random_race")
        languages = ti.xcom_pull(task_ids="languages")
        char_class = ti.xcom_pull(task_ids="random_class")
        proficiency_choices = ti.xcom_pull(task_ids="proficiency_choices")

        level = 1
        spells = []

        if not os.path.exists(csv_file):
            with open(csv_file, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([
                    "name", 
                    "attributes", 
                    "race", 
                    "languages", 
                    "class", 
                    "proficiency_choices", 
                    "level", 
                    "spells"
                ])

        # Append the new row
        with open(csv_file, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([name, attributes, race, languages, char_class, proficiency_choices, level, spells])

    def clean_list_field(value):
        if isinstance(value, list):
            return ", ".join(value)
        if isinstance(value, str):
            # Remove brackets and quotes
            value = value.strip("[]")
            value = value.replace("'", "").replace('"', "")
            return ", ".join([v.strip() for v in value.split(",") if v.strip()])
        return str(value)

    def _create_character_table(csv_file="/opt/airflow/data/characters.csv"):
        df = pd.read_csv(csv_file)

        sql_statements = [
            """
            CREATE TABLE IF NOT EXISTS character (
            name VARCHAR(255),
            attributes VARCHAR(255),
            race VARCHAR(255),
            languages VARCHAR(255),
            class VARCHAR(255),
            proficiency_choices VARCHAR(255),
            level VARCHAR(255),
            spells VARCHAR(255)
            );
            """
        ]
        
        with open("/opt/airflow/data/character_table.sql", "w") as f:
            f.write(
                "CREATE TABLE IF NOT EXISTS character (\n"
                "  name VARCHAR(255),\n"
                "  attributes VARCHAR(255),\n"
                "  race VARCHAR(255),\n"
                "  languages VARCHAR(255),\n"
                "  class VARCHAR(255),\n"
                "  proficiency_choices VARCHAR(255)\n"
                "  level VARCHAR(255)\n"
                "  spells VARCHAR(255)\n"
                ");\n"
            )
            for _, row in df.iterrows():
                name = row.get("name", "")
                attributes = row.get("attributes", "")
                race = row.get("race", "")
                languages = clean_list_field(row.get("languages", ""))
                char_class = row.get("class", "")
                proficiency_choices = clean_list_field(row.get("proficiency_choices", ""))
                level = row.get("level", "")
                spells = row.get("spells", "")

                f.write(
                    "INSERT INTO character VALUES ("
                    f"'{name}', '{attributes}', '{race}', '{languages}', "
                    f"'{char_class}', '{proficiency_choices}', '{level}', '{spells}'"
                    ");\n"
                )

                sql_statements.append(
                    f"INSERT INTO character VALUES ("
                    f"'{name}', '{attributes}', '{race}', '{languages}', "
                    f"'{char_class}', '{proficiency_choices}', '{level}', '{spells}');"
                )

        return "\n".join(sql_statements)


    # ------- TASKS -------------

    random_name = PythonOperator(
        task_id="random_name",
        python_callable=_random_name,
    )

    random_race = PythonOperator(
        task_id="random_race",
        python_callable=_random_race,
    )

    random_attributes = PythonOperator(
        task_id="random_attributes",
        python_callable=_random_attributes,
    )

    languages = PythonOperator(
        task_id="languages",
        python_callable=_languages_from_race,
    )

    random_class = PythonOperator(
        task_id="random_class",
        python_callable=_random_class,
    )

    proficiency_choices = PythonOperator(
        task_id="proficiency_choices",
        python_callable=_proficiency_choices_from_class,
    )

    add_character_in_csv = PythonOperator(
        task_id="add_character_in_csv",
        python_callable=_add_character_in_csv,
    )
    
    create_character_table = PythonOperator(
        task_id="create_character_table",
        python_callable=_create_character_table,
    )

    # ------- DB TASKS

    insert_inserts = SQLExecuteQueryOperator(
        task_id="insert_inserts",
        conn_id="postgres_not_default",
        sql="{{ ti.xcom_pull(task_ids='create_character_table') }}",
        autocommit=True,
    )

    random_name >> random_race >> languages >> random_attributes >> random_class >> proficiency_choices >> add_character_in_csv >> create_character_table >> insert_inserts 
    

    
