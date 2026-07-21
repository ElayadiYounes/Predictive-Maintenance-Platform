#!/bin/bash

set -eux

echo "========================================"
echo "Installing Apache Hive ${HIVE_VERSION}"
echo "========================================"

curl --fail \
     --location \
     --silent \
     --show-error \
     "https://archive.apache.org/dist/hive/hive-${HIVE_VERSION}/apache-hive-${HIVE_VERSION}-bin.tar.gz" \
     -o /tmp/hive.tar.gz

mkdir -p /opt

tar -xzf /tmp/hive.tar.gz -C /opt

mv /opt/apache-hive-${HIVE_VERSION}-bin "${HIVE_HOME}"

rm -f /tmp/hive.tar.gz

if [ ! -d "${HIVE_HOME}" ]; then
    echo "Hive installation failed."
    exit 1
fi

echo "========================================"
echo "Apache Hive installed successfully."
echo "========================================"