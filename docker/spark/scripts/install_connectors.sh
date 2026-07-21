#!/bin/bash

set -eux

JARS_DIR="${SPARK_HOME}/jars"

echo "========================================="
echo "Installing Spark connectors"
echo "========================================="

download_jar() {
    local url="$1"
    local output="$2"

    echo "Downloading $(basename "$output")"

    curl --fail \
         --location \
         --silent \
         --show-error \
         "$url" \
         -o "$output"
}

# Hadoop AWS
download_jar \
"https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/${HADOOP_AWS_VERSION}/hadoop-aws-${HADOOP_AWS_VERSION}.jar" \
"${JARS_DIR}/hadoop-aws.jar"

# AWS SDK Bundle
download_jar \
"https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/${AWS_SDK_VERSION}/aws-java-sdk-bundle-${AWS_SDK_VERSION}.jar" \
"${JARS_DIR}/aws-java-sdk-bundle.jar"

echo "All Spark connectors installed successfully."