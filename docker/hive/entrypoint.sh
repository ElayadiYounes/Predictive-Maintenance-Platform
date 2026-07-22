#!/bin/bash

set -e

echo "==========================================="
echo "OCP Predictive Maintenance Platform"
echo "Hive Metastore"
echo "Environment : ${APP_ENV}"
echo "==========================================="

echo "Generating hive-site.xml..."

tmp=$(mktemp)

envsubst < /opt/hive/conf/hive-site.xml > "$tmp"

mv "$tmp" /opt/hive/conf/hive-site.xml

echo "Configuration generated."

echo "Waiting for PostgreSQL..."
#!/bin/bash

set -e

echo "==========================================="
echo "OCP Predictive Maintenance Platform"
echo "Hive"
echo "Service     : ${HIVE_SERVICE}"
echo "Environment : ${APP_ENV}"
echo "==========================================="

echo "Generating hive-site.xml..."

tmp=$(mktemp)

envsubst < "${HIVE_HOME}/conf/hive-site.xml" > "${tmp}"

mv "${tmp}" "${HIVE_HOME}/conf/hive-site.xml"

echo "Configuration generated."

echo "Waiting for PostgreSQL..."

until nc -z "${POSTGRES_HOST}" "${POSTGRES_PORT}"
do
    sleep 2
done

echo "PostgreSQL is ready."

case "${HIVE_SERVICE}" in

    metastore)

        echo "Checking Hive schema..."

        if schematool \
            -dbType "${HIVE_METASTORE_DB_TYPE}" \
            -info > /dev/null 2>&1
        then
            echo "Hive schema already exists."
        else
            echo "Initializing Hive schema..."

            schematool \
                -dbType "${HIVE_METASTORE_DB_TYPE}" \
                -initSchema
        fi

        echo "Starting Hive Metastore..."

        exec hive --service metastore
        ;;

    server2)

        echo "Waiting for Hive Metastore..."

        until nc -z hive-metastore 9083
        do
            sleep 2
        done

        echo "Hive Metastore is ready."

        echo "Starting HiveServer2..."

        exec hive --service hiveserver2
        ;;

    *)

        echo "ERROR: Unknown HIVE_SERVICE : ${HIVE_SERVICE}"
        exit 1
        ;;

esac
until nc -z "${POSTGRES_HOST}" "${POSTGRES_PORT}"
do
    sleep 2
done

echo "PostgreSQL is ready."

echo "Checking Hive schema..."

if schematool \
    -dbType "${HIVE_METASTORE_DB_TYPE}" \
    -info > /dev/null 2>&1
then
    echo "Hive schema already exists."
else
    echo "Initializing Hive schema..."

    schematool \
        -dbType "${HIVE_METASTORE_DB_TYPE}" \
        -initSchema
fi

echo "Starting Hive Metastore..."

exec hive --service metastore