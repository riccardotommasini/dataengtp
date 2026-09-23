FROM apache/airflow:3.1.0

# Keep these in sync with the FROM tag above when bumping Airflow.
# PYTHON_VERSION must match the interpreter in the base image (3.1.0 ships 3.12)
# and is the suffix of the upstream constraints filename.
ARG AIRFLOW_VERSION=3.1.0
ARG PYTHON_VERSION=3.12

ADD requirements.txt .

# Constraints pin Airflow's own dependency tree to a known-good set.
# They are applied to the Airflow install only: requirements.txt holds course
# libraries whose versions intentionally differ from upstream constraints
# (e.g. pandas 2.2.2 vs the constrained 2.1.4), and constraining them would
# make the resolve fail.
RUN pip install --no-cache-dir \
      "apache-airflow==${AIRFLOW_VERSION}" \
      --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt" \
 && pip install --no-cache-dir -r requirements.txt
