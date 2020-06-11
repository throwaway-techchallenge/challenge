# Paranuara tech challenge
This project is an implementation of a tech challenge meant to import, clean and expose a foreign planet citizens data. 

- The project is written to resemble potential long-maintenance product but takes some reasonable shortcuts given that it's a tech challenge.
- There are some reasonable assumptions about state of other potential resource files that can be used for this project but basic data sanitation is implemented.
- The `index ` fields are treated as primary keys in the database and are assumed to be unique. See the "other commands" section at the end of this documentation to see how to purge the database in case you want to upload different data with the same `index` values.
- A relational database was used even though the data would be easier to import into a document-based database (e.g. MongoDB). This is because it allows much better guarantees in the future, despite initial normalisation cost. Postgres was chosen simply due to authors' best familiarity with it. MySql might be used instead with minimal changes.
- A potential improvement to error handling might be to lazily return all of the errors found, instead of eagerly returning the first one.
- Debug mode is left turned on for easier debugging if there happen to be uncaught bugs in the project. Standard Django authentication middleware and apps are left in - they are not being used in the project but would be the very next step if this was to become a more feature rich project. A lot of Django default settings are left for that reason - it seems excessive and unnecessary to trim them to the absolute minimum at this point.  

## API endpoints
- ### `citizens/<citizen_id>/`
    Provides some basic data about the Citizen and a list of fruits and vegetables they like.
    Example response:
    ```
    {
        "username": "Ahi",
        "age": "30",
        "fruits": ["banana", "apple"],
        "vegetables": ["beetroot", "lettuce"]
    }
    ```
    Returns a **404** error if id is not found in the database or **400** if the id is not an integer.

- ### `citizens/<citizen_a_id>/<citizen_b_id>/`
    Provides some basic data about Citizen A and Citizen B and a list of their common friends that are alive and have brown eyes:
    Example response:
    ```
        {
        "citizens": [
            {
                "username": "Decker Mckenzie",
                "age": 60,
                "address": "492 Stockton Street, Lawrence, Guam, 4854",
                "phone_number": "+1 (893) 587-3311"
            },
            {
                "username": "Bonnie Bass", "age": 54,
                "address": "455 Dictum Court, Nadine, Mississippi, 6499",
                "phone_number": "+1 (823) 428-3710"
            }
        ],
        "common_live_brown_eyed_friends": [
            {
                "username": "Decker Mckenzie",
                "age": 60,
                "address": "492 Stockton Street, Lawrence, Guam, 4854",
                "phone_number": "+1 (893) 587-3311"
            }
        ]
    }
    ```
    Returns a **404** error if any of the ids is not found in the database or **400** if any of the the id is not an integer.

- ### `company_employees/<company_id>/`
    Provides a list of links into company's employees' detail views.
    Example response:
    ```
    {
        "employees": [
            "http://localhost:8001/citizens/287/",
            "http://localhost:8001/citizens/332/",
            "http://localhost:8001/citizens/382/",
            "http://localhost:8001/citizens/531/",
            "http://localhost:8001/citizens/703/",
            "http://localhost:8001/citizens/804/",
            "http://localhost:8001/citizens/935/"
        ]
    }
    ```
    Returns a **404** error if id is not found in the database,  **400** if the id is not an integer.

## Installation instructions

All installation instructions assume bash shell. Run all commands from the command line.

 1. Create a new, empty directory and navigate to it:
 
    `mkdir temporary-challenge-directory ; cd temporary-challenge-directory`

2. Clone the repository into the directory:

    `git clone git@github.com:throwaway-techchallenge/challenge.git`

3. Install postgres:

    *Note: this step might be cleaner on the host system by using docker containers but this approach was chosen to allow for control over the database directly from host OS without additional configuration.*

    3.a. On MacOs:
    
    `brew install postgresql@11`
    
    `export PATH="/usr/local/opt/postgresql@11/bin:$PATH"`

    3.b. On a recent Debian distribution:
    
    `sudo apt update ; sudo apt-get install postgresql-11`

    3.c. For different Linux distros, please see: [https://www.postgresql.org/download/linux/](https://www.postgresql.org/download/linux/)

4. Create the database and user:

    ```
    initdb -D paranuara_db
    pg_ctl -D paranuara_db -l logfile start

    createdb paranuara_db
    createuser 'checktoporov'
    psql -d paranuara_db -c 'ALTER USER checktoporov WITH SUPERUSER'
    ```
5. Create and activate python virtual environment

    `python -m venv paranuara_venv ; source paranuara_venv/bin/activate`

6. Install python dependencies:

    `pip install -r challenge/requirements.txt`

7. Populate the database with provided resources:

    `./challenge/paranuara/manage.py import_resources`

8. Run test server:

    `./challenge/paranuara/manage.py runserver localhost:8000`

## Other commands
- Undo the resource import (e.g. to import differend data using the same with the same indexes): 

    `./challenge/paranuara/manage.py purge_database`

- Run tests:

    `cd challenge/paranuara` (the test command needs to be ran from the project directory)
    
    `./manage.py test`

