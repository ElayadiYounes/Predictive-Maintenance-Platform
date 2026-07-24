#!/bin/bash

set -eux

echo "========================================="
echo "Installing Spark connectors"
echo "========================================="

JARS_DIR="${SPARK_HOME}/jars"

# ========================================
# Check Spark installation
# ========================================

test -d "${SPARK_HOME}"

mkdir -p "${JARS_DIR}"

# ========================================
# Check required files
# ========================================

test -f "/tmp/hadoop-aws-${HADOOP_AWS_VERSION}.jar"

test -f "/tmp/aws-java-sdk-bundle-${AWS_SDK_VERSION}.jar"

# ========================================
# Install connectors
# ========================================

cp "/tmp/hadoop-aws-${HADOOP_AWS_VERSION}.jar" \
   "${JARS_DIR}/"

cp "/tmp/aws-java-sdk-bundle-${AWS_SDK_VERSION}.jar" \
   "${JARS_DIR}/"

# ========================================
# Cleanup
# ========================================

rm -f "/tmp/hadoop-aws-${HADOOP_AWS_VERSION}.jar"

rm -f "/tmp/aws-java-sdk-bundle-${AWS_SDK_VERSION}.jar"

echo
echo "Installed connectors:"
ls -lh "${JARS_DIR}" | grep -E "hadoop-aws|aws-java-sdk"

echo
echo "Spark connectors installed successfully."