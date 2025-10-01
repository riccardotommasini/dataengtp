
# Task 1 - fetch the current [ISS](http://api.open-notify.org/iss-now.json) location and save it as a file

# Task 2 - find the closest country, save it to a file

# Task 3 - save the closest country information to the database (you can reuse the airflow one for this time)

# Task 4 - output the continent

Notably, for task 3 you need to use a PostgresOperator

```python
atask = PostgresOperator(
    task_id='taskid',
    dag=your_dag,
    postgres_conn_id='database address',
    sql='SQL Script',
    trigger_rule='none_failed',
    autocommit=True,
)
