#!/bin/bash

set -e

echo "====================================="
echo "OCP Predictive Maintenance Platform"
echo "Spark Node"
echo "Role : ${SPARK_MODE}"
echo "====================================="

echo "Generating Spark configuration..."

for file in \
    /opt/spark/conf/spark-defaults.conf \
    /opt/spark/conf/hive-site.xml
do
    tmp=$(mktemp)
    envsubst < "$file" > "$tmp"
    mv "$tmp" "$file"
done

echo "Java version:"
java -version

echo
echo "Spark version:"
spark-submit --version

echo
echo "Installed S3A connectors:"
ls /opt/spark/jars | grep -E "hadoop-aws|aws-java-sdk" || true

echo
echo "Container ready."

#################################################################################################

if [ -z "${SPARK_MODE}" ]; then
    echo "ERROR: SPARK_MODE is not defined."
    exit 1
fi

case "${SPARK_MODE}" in

    master)

        echo "Starting Spark Master..."

        spark-class \
              org.apache.spark.deploy.master.Master \
              --host "${SPARK_MASTER_HOST}" \
              --port "${SPARK_MASTER_PORT}" \
              --webui-port "${SPARK_MASTER_WEBUI_PORT}"
        ;;

    worker)

        if [ -z "${SPARK_MASTER_URL}" ]; then
            echo "ERROR: SPARK_MASTER_URL is not defined."
            exit 1
        fi

        echo "Starting Spark Worker..."

        exec spark-class \
            org.apache.spark.deploy.worker.Worker \
            --webui-port "${SPARK_WORKER_WEBUI_PORT}" \
            "${SPARK_MASTER_URL}"
        ;;

    *)

        echo "ERROR: Unknown SPARK_MODE : ${SPARK_MODE}"
        exit 1
        ;;

esac