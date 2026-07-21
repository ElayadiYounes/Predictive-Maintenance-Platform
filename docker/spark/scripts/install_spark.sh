#!/bin/bash

set -eux

echo "========================================="
echo "Installing Apache Spark ${SPARK_VERSION}"
echo "========================================="

curl --fail \
     --location \
     --silent \
     --show-error \
"https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz" \
-o /tmp/spark.tgz

tar -xzf /tmp/spark.tgz -C /opt

mv "/opt/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}" "${SPARK_HOME}"

rm /tmp/spark.tgz

echo "Apache Spark installed successfully."

spark-submit --version