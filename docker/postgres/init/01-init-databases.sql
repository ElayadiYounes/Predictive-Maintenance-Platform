SELECT 'CREATE DATABASE hive_metastore'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'hive_metastore'
)\gexec

SELECT 'CREATE DATABASE airflow'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'airflow'
)\gexec

SELECT 'CREATE DATABASE metabase_db'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'metabase_db'
)\gexec