## Home assignment

You need to create 2 DAGs:
1) "CRM generator"
    Per execution, fetch 5 users from the API at https://randomuser.me/
    Save the users into a csv file.
2) "User age trend"
    Set up a sensor so that the DAG is triggered once the csv file in 1) has been created.
    Save the users from the csv file into a SQL table.
    Calculate the average of the users.
    Use branching to alert whether the average age of the users is increasing or decreasing compared to previous execution.
    HINT: [video on sensors](https://www.youtube.com/watch?v=gSdy3Jxk75k)
    
