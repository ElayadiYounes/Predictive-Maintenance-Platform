#!/bin/bash

set -eux

echo "======================================"
echo "Installing Apache Spark ${SPARK_VERSION}"
echo "======================================"

curl --fail --location --silent --show-error \
https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz \
-o /tmp/spark.tgz

tar -xzf /tmp/spark.tgz -C /opt

if [ ! -d "/opt/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}" ]; then
    echo "Spark extraction failed."
    exit 1
fi

mv "/opt/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}" "${SPARK_HOME}"

chown -R airflow:root "${SPARK_HOME}"

rm /tmp/spark.tgz

echo "Spark version:"
spark-submit --version

echo "======================================"
echo "Apache Spark installed successfully"
echo "======================================"