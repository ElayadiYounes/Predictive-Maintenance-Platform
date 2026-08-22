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
        echo "+++++++Verification++++++++"
        echo "SPARK_MASTER_HOST=${SPARK_MASTER_HOST}"
        echo "SPARK_MASTER_PORT=${SPARK_MASTER_PORT}"

        /opt/spark/sbin/start-master.sh \
              --host "${SPARK_MASTER_HOST}" \
              --port "${SPARK_MASTER_PORT}" \
              --webui-port "${SPARK_MASTER_WEBUI_PORT}"

        echo "Starting Spark Thrift Server for Metabase on port 10016..."
        /opt/spark/sbin/start-thriftserver.sh \
              --master "spark://${SPARK_MASTER_HOST}:${SPARK_MASTER_PORT}" \
              --hiveconf hive.server2.thrift.port=10016 \
              --conf spark.cores.max=4 \
              --conf spark.executor.cores=2 \
              --conf spark.executor.memory=1g

        # 3. CRUCIAL : On maintient le conteneur Docker actif en surveillant les logs de Spark
        echo "Monitoring Spark logs to keep container alive..."
        tail -f /opt/spark/logs/*

        ;;

    worker)

        if [ -z "${SPARK_MASTER_URL}" ]; then
            echo "ERROR: SPARK_MASTER_URL is not defined."
            exit 1
        fi

        echo "Starting Spark Worker..."
         echo "+++++++Verification++++++++"
        echo "SPARK_WORKER_WEBUI_PORT=${SPARK_WORKER_WEBUI_PORT}"
        echo "SPARK_MASTER_URL=${SPARK_MASTER_URL}"
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