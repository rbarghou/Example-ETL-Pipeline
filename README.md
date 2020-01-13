# Example-ETL-Pipeline

## Overview.
This is an ETL pipeline meant to demonstrate converting from a relational db format to a flat schema while enriching the data.

This example uses the concepts of a biological laboratory for it's underlying concepts: Samples, Measurements and Experiments.

Imagine a Biological Laboratory where scientists conduct experiments which produce samples.  Samples can also be used to create more samples, leading to a tree data structure.  Multiple measurements of these samples can be taken. New experiments are conducted and the samples they produce are being added to the system.  New measurements are being taken which can be novel new measurement types.  The scientists want to conduct analytics on the data but they don't want to have to join the data in their analytics system.  They want to be able to work on a flat single-table schema.

This is where this pipeline is able to help.

This pipeline is able move data from relational tables of `Samples` and `SampleMeasurements` into the dynamically created table of `ExperimentMeasurements`

When this pipeline is run, it _extracts_ data from the `Samples` and `SampleMeasurement` tables and then _transforms_ it into the format used in `ExperimentMeasurements` and then _loads_ it into this table.  It then _enriches_ the data by populating the _root sample_ of every tree of samples.

## Prerequisites

This repository depends on the use of `docker` and `docker-compose`.

Installation instructions can be found here:

- [Docker](https://docs.docker.com/v17.09/engine/installation/)
- [docker-compose](https://docs.docker.com/compose/install/)

Additionally, the instructions for this demo will assume that you have are
using a linux-like environment. This was developed on hardware running
Ubuntu 19.10 and has not been tested in other operating systems.

## Quickstart
If you just want to run the demo - these are the relevant commands

```
# Bring up and down - You shouldn't need any environment variables set.
> docker-compose up -d
> docker-compose down

# Run the tests which also generates test data of various sizes
> docker exec -it etl_app bash -c "pytest ./tests/test_pipeline.py"

# Refresh the database to a consistent state
> docker exec -it etl_app bash -c "./scripts/refresh_database.sh"

# Enter the cli for the mysql engine
> docker exec -it etl_db bash -c "mysql -u etl -D etl_db -pasdfasdf"

# Inspect database
mysql> show tables;
mysql> describe samples;
mysql> describe sample_measurements;
mysql> describe experiment_measurements;
mysql> select * from samples limit 20;
mysql> select * from sample_measurements limit 20;
mysql> select * from experiment_measurements limit 20;
```
For more detailed instructions skip down to the instructions section

## Technologies
* Docker / docker-compose
* SQLAlchemy / Alembic
* MySQL

## Important modules

### [./app/schema.py](https://github.com/rbarghou/Example-ETL-Pipeline/blob/master/app/schema.py)
Contains 3 tables: `Sample`, `SampleMeasurement`, `ExperimentMeasurement`
The first 2 are static schema, but the 3rd is dynamically generated using SQLAlchemy's `automap_base`

### [./app/etl.py](https://github.com/rbarghou/Example-ETL-Pipeline/blob/master/app/etl.py)
Contains the actual ETL steps and a description of how to organize them in an Airflow DAG.

### [./tests/generate.py](https://github.com/rbarghou/Example-ETL-Pipeline/blob/master/tests/generate.py)
Contains the code for generating test data for the demonstration.


## Instructions

To begin, navigate in a `bash`-like terminal to the root of this repository

To perform the basic demo there are 4 basic steps

1. Bring up the services.
2. Run the test which generate the test data
3. Examine the results using either sqlalchemy or mysql
4. Bring down services

Additionally, you may repeat steps 2 as many times as you like. While the
generated data is random, the randomizer uses a fixed seed, so you should
get consistent results.

### Step 1: Bring up the services

```
> docker-compose up -d
...
Creating network "example-etl-pipeline_default" with the default driver
Creating example-etl-pipeline_etl_db ... done
Creating example-etl-pipeline_etl_app ... done
```

This will create:

- 1 network
- 1 volume
- 1 database service: etl_db
- 1 application service: etl_app

### Step 2: Execute tests

In this case, I recommend using the `docker exec` command to either
directly run the tests or to enter the pod to run the tests. My preferred
method is as follows

```
> docker exec -it etl_app bash
root@asdf1234:/etl# pytest -s -v ./tests/test_pipeline.py
```

This should execute test which removes all the tables (except those used by
alembic to manage migrations) from the database and the reruns the migrations.

For more information on the migrations and test data refer to the following
files:

./scripts/recreate_database.sh
./versions/31cb73361b6f_added_experiment_measurements_table.py
./versions/64f0cb642938_task_1_create_tables.py
./versions/task_1_create_tables.sql
./tests/conftest.py
./tests/generate.py

This test will run multiple times with different generated data size, 1,000,
10,000, 100,000 records.

For more information on what is specifically run in this test refer to this file
./tests/test_pipeline.py

I will go into more information about the structure of the pipeline later.

### step 3: Inspect Results

```
> docker exec -it etl_db bash -c "mysql -u etl -D etl_db -pasdfasdf"
mysql: [Warning] Using a password on the command line interface can be insecure.
Reading table information for completion of table and column names
You can turn off this feature to get a quicker startup with -A

Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 22
Server version: 8.0.18 MySQL Community Server - GPL

Copyright (c) 2000, 2019, Oracle and/or its affiliates. All rights reserved.

Oracle is a registered trademark of Oracle Corporation and/or its
affiliates. Other names may be trademarks of their respective
owners.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql>
```

**Please note that I am using very insecure passwords. I considered the use
of more sophisticated secrets management out of the scope of this exercise**

at this point you should be able to inspect the database structure more
thoroughly.

for example:

```
> docker exec -it etl_db bash -c "mysql -u etl -Detl_db -pasdfasdf"
mysql: [Warning] Using a password on the command line interface can be insecure.
Reading table information for completion of table and column names
You can turn off this feature to get a quicker startup with -A

Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 24
Server version: 8.0.18 MySQL Community Server - GPL

Copyright (c) 2000, 2019, Oracle and/or its affiliates. All rights reserved.

Oracle is a registered trademark of Oracle Corporation and/or its
affiliates. Other names may be trademarks of their respective
owners.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql> show tables;
+-------------------------+
| Tables_in_etl_db     |
+-------------------------+
| alembic_version         |
| experiment_measurements |
| sample_measurements     |
| samples                 |
+-------------------------+
4 rows in set (0.01 sec)

mysql> describe samples;
+---------------+-----------+------+-----+-------------------+-------------------+
| Field         | Type      | Null | Key | Default           | Extra             |
+---------------+-----------+------+-----+-------------------+-------------------+
| id            | int(11)   | NO   | PRI | NULL              | auto_increment    |
| parent_id     | int(11)   | YES  | MUL | NULL              |                   |
| experiment_id | int(11)   | YES  |     | NULL              |                   |
| ts            | timestamp | NO   |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
+---------------+-----------+------+-----+-------------------+-------------------+
4 rows in set (0.01 sec)

mysql> describe sample_measurements;
+------------------+---------------+------+-----+---------+-------+
| Field            | Type          | Null | Key | Default | Extra |
+------------------+---------------+------+-----+---------+-------+
| sample_id        | int(11)       | YES  | MUL | NULL    |       |
| measurement_type | varchar(10)   | YES  |     | NULL    |       |
| value            | decimal(16,6) | YES  |     | NULL    |       |
+------------------+---------------+------+-----+---------+-------+
3 rows in set (0.01 sec)

mysql> describe experiment_measurements;
+-------------------+---------------+------+-----+---------+-------+
| Field             | Type          | Null | Key | Default | Extra |
+-------------------+---------------+------+-----+---------+-------+
| experiment_id     | int(11)       | YES  |     | NULL    |       |
| top_parent_id     | int(11)       | YES  | MUL | NULL    |       |
| sample_id         | int(11)       | NO   | PRI | NULL    |       |
| measurement_area  | decimal(16,6) | YES  |     | NULL    |       |
| measurement_ph    | decimal(16,6) | YES  |     | NULL    |       |
| measurement_len   | decimal(16,6) | YES  |     | NULL    |       |
| measurement_smoot | decimal(16,6) | YES  |     | NULL    |       |
| measurement_foo   | decimal(16,6) | YES  |     | NULL    |       |
| measurement_vol   | decimal(16,6) | YES  |     | NULL    |       |
| measurement_bar   | decimal(16,6) | YES  |     | NULL    |       |
+-------------------+---------------+------+-----+---------+-------+
10 rows in set (0.00 sec)

mysql>


```

Additionally you can use this interface to confirm the validity of the
etl process according to the coding challenge.

```
mysql> select * from samples limit 20;
+----+-----------+---------------+---------------------+
| id | parent_id | experiment_id | ts                  |
+----+-----------+---------------+---------------------+
|  1 |      NULL |             1 | 2019-12-09 19:56:34 |
|  2 |         1 |             1 | 2019-12-09 19:56:34 |
|  3 |         1 |             1 | 2019-12-09 19:56:34 |
|  4 |         1 |             1 | 2019-12-09 19:56:34 |
|  5 |      NULL |             1 | 2019-12-09 19:56:34 |
|  6 |         2 |             1 | 2019-12-09 19:56:34 |
|  7 |         5 |             1 | 2019-12-09 19:56:34 |
|  8 |         7 |             1 | 2019-12-09 19:56:34 |
|  9 |         2 |             1 | 2019-12-09 19:56:34 |
| 10 |         9 |             1 | 2019-12-09 19:56:34 |
| 11 |        10 |             1 | 2019-12-09 19:56:34 |
| 12 |         9 |             1 | 2019-12-09 19:56:34 |
| 13 |      NULL |             2 | 2019-12-09 19:56:34 |
| 14 |        13 |             2 | 2019-12-09 19:56:34 |
| 15 |        13 |             2 | 2019-12-09 19:56:34 |
| 16 |        13 |             2 | 2019-12-09 19:56:34 |
| 17 |        10 |             1 | 2019-12-09 19:56:34 |
| 18 |        17 |             1 | 2019-12-09 19:56:34 |
| 19 |        17 |             1 | 2019-12-09 19:56:34 |
| 20 |        11 |             1 | 2019-12-09 19:56:34 |
+----+-----------+---------------+---------------------+
20 rows in set (0.00 sec)

mysql> select * from sample_measurements limit 20;
+-----------+------------------+------------+
| sample_id | measurement_type | value      |
+-----------+------------------+------------+
|         2 | vol              | 500.000000 |
|         3 | vol              | 400.000000 |
|         6 | vol              |  51.000000 |
|         9 | vol              |  50.000000 |
|        10 | vol              |  10.500000 |
|        12 | vol              |  40.300000 |
|        17 | vol              |  10.200000 |
|         8 | vol              |  40.800000 |
|        19 | vol              |  10.000000 |
|        20 | vol              |  40.700000 |
|         2 | ph               |   5.000000 |
|         3 | ph               |   7.000000 |
|         6 | ph               |   5.100000 |
|         9 | ph               |   7.200000 |
|        10 | ph               |   5.200000 |
|        12 | ph               |   7.400000 |
|        17 | ph               |   5.000000 |
|         8 | ph               |   7.400000 |
|        19 | ph               |   5.250000 |
|        20 | ph               |   7.340000 |
+-----------+------------------+------------+
20 rows in set (0.00 sec)

mysql> select * from experiment_measurements limit 20;
+---------------+---------------+-----------+-----------------+----------------+------------------+-----------------+-----------------+-------------------+-----------------+
| experiment_id | top_parent_id | sample_id | measurement_len | measurement_ph | measurement_area | measurement_foo | measurement_bar | measurement_smoot | measurement_vol |
+---------------+---------------+-----------+-----------------+----------------+------------------+-----------------+-----------------+-------------------+-----------------+
|             1 |             1 |         1 |            NULL |           NULL |             NULL |            NULL |            NULL |              NULL |            NULL |
|             1 |             1 |         2 |            NULL |       5.000000 |             NULL |            NULL |            NULL |              NULL |      500.000000 |
|             1 |             1 |         3 |            NULL |       7.000000 |             NULL |            NULL |            NULL |              NULL |      400.000000 |
|             1 |             1 |         4 |            NULL |           NULL |             NULL |            NULL |            NULL |              NULL |            NULL |
|             1 |             5 |         5 |            NULL |           NULL |             NULL |            NULL |            NULL |              NULL |            NULL |
|             1 |             1 |         6 |            NULL |       5.100000 |             NULL |            NULL |            NULL |              NULL |       51.000000 |
|             1 |             5 |         7 |            NULL |           NULL |             NULL |            NULL |            NULL |              NULL |            NULL |
|             1 |             5 |         8 |            NULL |       7.400000 |             NULL |            NULL |            NULL |              NULL |       40.800000 |
|             1 |             1 |         9 |            NULL |       7.200000 |             NULL |            NULL |            NULL |              NULL |       50.000000 |
|             1 |             1 |        10 |            NULL |       5.200000 |             NULL |            NULL |            NULL |              NULL |       10.500000 |
|             1 |             1 |        11 |            NULL |           NULL |             NULL |            NULL |            NULL |              NULL |            NULL |
|             1 |             1 |        12 |            NULL |       7.400000 |             NULL |            NULL |            NULL |              NULL |       40.300000 |
|             2 |            13 |        13 |            NULL |           NULL |             NULL |            NULL |            NULL |              NULL |            NULL |
|             2 |            13 |        14 |            NULL |           NULL |             NULL |            NULL |            NULL |              NULL |            NULL |
|             2 |            13 |        15 |            NULL |           NULL |             NULL |            NULL |            NULL |              NULL |            NULL |
|             2 |            13 |        16 |            NULL |           NULL |             NULL |            NULL |            NULL |              NULL |            NULL |
|             1 |             1 |        17 |            NULL |       5.000000 |             NULL |            NULL |            NULL |              NULL |       10.200000 |
|             1 |             1 |        18 |            NULL |           NULL |             NULL |            NULL |            NULL |              NULL |            NULL |
|             1 |             1 |        19 |            NULL |       5.250000 |             NULL |            NULL |            NULL |              NULL |       10.000000 |
|             1 |             1 |        20 |            NULL |       7.340000 |             NULL |            NULL |            NULL |              NULL |       40.700000 |
+---------------+---------------+-----------+-----------------+----------------+------------------+-----------------+-----------------+-------------------+-----------------+
20 rows in set (0.00 sec)

mysql>
```

Note that the additional columns of different measurement types demonstrate
that the etl pipeline is capable of dynamically adding columns to the
experiment_measurements table as specified in the challenge text.

### Step 4: Tear Down Demo and free resources

After you have investigated the demo to your satisfaction, you can bring down
the services and free up your resources as follows

```
> docker-compose down --remove-orphans
Stopping etl_app ... done
Stopping etl_db  ... done
Removing etl_app ... done
Removing etl_db  ... done
Removing network etl-coding-challenge_default
```

You may also want to remove images and volumes you've build from docker using
this command

```
> docker image rm example-etl-pipeline_etl_app
> docker volume rm example-etl-pipeline_etl_db
```

## Conclusion and Further Work

This demo should illustrate an approach to the Coding Challenge. It attempts
to balance performance, deployability, compatibility and extensibility.

Further work that could be built on this project would include:

- Integration with Airflow
- Data Integrity checks
- Data Upload endpoints
- Admin portal
