#!/bin/bash

set -euo pipefail

JARS_DIR="${SPARK_HOME}/jars"

echo "========================================="
echo "Installing Spark connectors"
echo "========================================="

if [ ! -d "${SPARK_HOME}" ]; then
    echo "ERROR: SPARK_HOME not found."
    exit 1
fi

mkdir -p "${JARS_DIR}"

download_jar() {

    local url="$1"
    local output="$2"

    if [ -f "$output" ]; then
        echo "$(basename "$output") already installed."
        return
    fi

    echo "Downloading $(basename "$output")..."

    curl \
        --fail \
        --location \
        --silent \
        --show-error \
        "$url" \
        -o "$output"
}

download_jar \
"https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/${HADOOP_AWS_VERSION}/hadoop-aws-${HADOOP_AWS_VERSION}.jar" \
"${JARS_DIR}/hadoop-aws.jar"

download_jar \
"https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/${AWS_SDK_VERSION}/aws-java-sdk-bundle-${AWS_SDK_VERSION}.jar" \
"${JARS_DIR}/aws-java-sdk-bundle.jar"

echo
echo "Installed connectors:"
ls -lh "${JARS_DIR}" | grep -E "hadoop-aws|aws-java-sdk"

echo
echo "Spark connectors installed successfully."