#!/bin/bash

set -eux

echo "========================================"
echo "Installing PostgreSQL JDBC Driver"
echo "========================================"

curl --fail \
     --location \
     --silent \
     --show-error \
     "https://jdbc.postgresql.org/download/postgresql-${POSTGRES_JDBC_VERSION}.jar" \
     -o "${HIVE_HOME}/lib/postgresql.jar"

if [ ! -f "${HIVE_HOME}/lib/postgresql.jar" ]; then
    echo "PostgreSQL JDBC Driver installation failed."
    exit 1
fi

echo "========================================"
echo "PostgreSQL JDBC Driver installed."
echo "========================================"