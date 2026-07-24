#!/bin/bash

set -eux

echo "========================================"
echo "Installing Apache Hadoop ${HADOOP_VERSION}"
echo "========================================"

# ========================================
# Check required files
# ========================================

test -f "/tmp/hadoop-${HADOOP_VERSION}.tar.gz"
test -f "/tmp/hadoop-aws-${HADOOP_VERSION}.jar"
test -f "/tmp/aws-java-sdk-bundle-${AWS_SDK_VERSION}.jar"

# ========================================
# Install Hadoop
# ========================================

mkdir -p /opt

tar -xzf "/tmp/hadoop-${HADOOP_VERSION}.tar.gz" \
    -C /opt

test -d "/opt/hadoop-${HADOOP_VERSION}"

mv "/opt/hadoop-${HADOOP_VERSION}" \
   "${HADOOP_HOME}"

# ========================================
# Install S3A connectors
# ========================================

cp "/tmp/hadoop-aws-${HADOOP_VERSION}.jar" \
   "${HADOOP_HOME}/share/hadoop/tools/lib/"

cp "/tmp/aws-java-sdk-bundle-${AWS_SDK_VERSION}.jar" \
   "${HADOOP_HOME}/share/hadoop/tools/lib/"

# ========================================
# Copy connectors to Hive
# ========================================

cp "/tmp/hadoop-aws-${HADOOP_VERSION}.jar" \
   "${HIVE_HOME}/lib/"

cp "/tmp/aws-java-sdk-bundle-${AWS_SDK_VERSION}.jar" \
   "${HIVE_HOME}/lib/"

# ========================================
# Cleanup
# ========================================

rm -f \
    "/tmp/hadoop-${HADOOP_VERSION}.tar.gz" \
    "/tmp/hadoop-aws-${HADOOP_VERSION}.jar" \
    "/tmp/aws-java-sdk-bundle-${AWS_SDK_VERSION}.jar"

echo "========================================"
echo "Apache Hadoop installed successfully"
echo "========================================"

"${HADOOP_HOME}/bin/hadoop" version

"${HIVE_HOME}/bin/hive" --version