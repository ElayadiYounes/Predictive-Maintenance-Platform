#!/bin/bash

set -eux

echo "======================================"
echo "Installing Apache Spark ${SPARK_VERSION}"
echo "======================================"

ARCHIVE="/tmp/spark-${SPARK_VERSION}-bin-hadoop${SPARK_HADOOP_PROFILE}.tgz"

# ========================================
# Check required file
# ========================================

test -f "${ARCHIVE}"

# ========================================
# Install Spark
# ========================================

mkdir -p /opt

tar -xzf "${ARCHIVE}" -C /opt

test -d "/opt/spark-${SPARK_VERSION}-bin-hadoop${SPARK_HADOOP_PROFILE}"

mv \
"/opt/spark-${SPARK_VERSION}-bin-hadoop${SPARK_HADOOP_PROFILE}" \
"${SPARK_HOME}"

rm -f "${ARCHIVE}"

chown -R airflow:root "${SPARK_HOME}"

echo "======================================"
echo "Apache Spark installed successfully"
echo "======================================"

"${SPARK_HOME}/bin/spark-submit" --version