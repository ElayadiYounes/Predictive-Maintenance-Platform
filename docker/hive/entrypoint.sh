#!/bin/bash

set -e

# === ARCHITECTURE CONFIGURATION JAVA 8 ===
export HIVE_OPTS=""
export HIVE_DEBUG="false"

export HIVE_HOME="${HIVE_HOME:-/opt/hive}"
export HADOOP_HOME="${HADOOP_HOME:-/opt/hadoop}"
export JAVA_HOME="${JAVA_HOME:-/opt/java/openjdk}"

export HADOOP_CLASSPATH="${HADOOP_HOME}/share/hadoop/tools/lib/*"

export PATH="${HIVE_HOME}/bin:${HADOOP_HOME}/bin:${JAVA_HOME}/bin:${PATH}"

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

echo "======================================"
echo "POSTGRES_HOST=${POSTGRES_HOST}"
echo "POSTGRES_PORT=${POSTGRES_PORT}"
echo "POSTGRES_USER=${POSTGRES_USER}"
echo "POSTGRES_HIVE_DATABASE=${POSTGRES_HIVE_DATABASE}"
echo "MINIO_HOST=${MINIO_HOST}"
echo "MINIO_API_PORT=${MINIO_API_PORT}"
echo "HIVE_SERVICE=${HIVE_SERVICE}"
echo "======================================"

echo "Waiting for PostgreSQL..."

until nc -z "${POSTGRES_HOST}" "${POSTGRES_PORT}"
do
    sleep 2
done

echo "PostgreSQL is ready."
echo "======================================"
echo "Checking Hive installation..."
echo "HIVE_HOME=${HIVE_HOME}"
echo "HADOOP_HOME=${HADOOP_HOME}"
echo "JAVA_HOME=${JAVA_HOME}"
echo "PATH=${PATH}"

echo "Checking Beeline..."
if command -v beeline >/dev/null 2>&1; then
    echo "Beeline found: $(command -v beeline)"

    beeline --version || true

else
    echo "ERROR: Beeline not found in PATH."
    ls -la "${HIVE_HOME}/bin/beeline" || true
    exit 1
fi



case "${HIVE_SERVICE}" in

    metastore)
      echo "Listing PostgreSQL drivers..."

      find ${HIVE_HOME}/lib -name "*postgres*"

       echo
       echo "Jar version :"

       ls -lh ${HIVE_HOME}/lib/postgresql.jar
       echo "Searching old postgres drivers"

       find ${HIVE_HOME}/lib -name "*jdbc*"

      find ${HIVE_HOME}/lib -name "*postgresql*"

        echo "Checking Hive schema..."

        if  "${HIVE_HOME}/bin/schematool" \
            -dbType "${HIVE_METASTORE_DB_TYPE}" \
            -info > /dev/null 2>&1
        then
            echo "Hive schema already exists."
        else
            echo "Initializing Hive schema..."

            "${HIVE_HOME}/bin/schematool" \
                -dbType "${HIVE_METASTORE_DB_TYPE}" \
                -initSchema
        fi

        echo "Starting Hive Metastore..."
        echo "Checking S3A jars..."

         ls -l ${HADOOP_HOME}/share/hadoop/tools/lib | grep aws || true

         ls -l ${HADOOP_HOME}/share/hadoop/tools/lib | grep bundle || true

         ls -l ${HADOOP_HOME}/share/hadoop/tools/lib | grep hadoop-aws || true
         echo "HADOOP_CLASSPATH=${HADOOP_CLASSPATH}"
          echo "===== DEBUG ====="

          echo "HADOOP_HOME=$HADOOP_HOME"

          echo "PATH=$PATH"

          ls -l /opt

          ls -l /opt/hadoop

          ls -l /opt/hadoop/bin

         which hadoop || true

         echo "================="
          hadoop classpath

        exec "${HIVE_HOME}/bin/hive" --service metastore
        ;;

    server2)

        echo "Waiting for Hive Metastore..."

        until nc -z hive-metastore 9083
        do
            sleep 2
        done

        echo "Hive Metastore is ready."

        echo "Starting HiveServer2..."

        exec "${HIVE_HOME}/bin/hive" --service hiveserver2
        ;;

    *)

        echo "ERROR: Unknown HIVE_SERVICE: ${HIVE_SERVICE}"
        exit 1
        ;;

esac