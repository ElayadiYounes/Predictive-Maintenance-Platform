#!/bin/bash

set -e

echo "==========================================="
echo "OCP Predictive Maintenance Platform"
echo "Hive Metastore"
echo "==========================================="

echo "Waiting PostgreSQL..."

until nc -z "${POSTGRES_HOST}" "${POSTGRES_PORT}"
do
    sleep 2
done

echo "PostgreSQL is ready."

echo "Checking Hive schema..."

if schematool \
    -dbType postgres \
    -info > /dev/null 2>&1
then
    echo "Hive schema already exists."
else
    echo "Initializing Hive schema..."

    schematool \
        -dbType postgres \
        -initSchema
fi

echo "Starting Hive Metastore..."

exec hive \
    --service metastore