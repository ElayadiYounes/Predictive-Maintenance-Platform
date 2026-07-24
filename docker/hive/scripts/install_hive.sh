#!/bin/bash

set -eux

echo "========================================"
echo "Installing Apache Hive ${HIVE_VERSION}"
echo "========================================"

# ========================================
# Check required file
# ========================================

test -f "/tmp/apache-hive-${HIVE_VERSION}-bin.tar.gz"

# ========================================
# Install Hive
# ========================================

mkdir -p /opt

tar -xzf "/tmp/apache-hive-${HIVE_VERSION}-bin.tar.gz" \
    -C /opt

test -d "/opt/apache-hive-${HIVE_VERSION}-bin"

mv "/opt/apache-hive-${HIVE_VERSION}-bin" \
   "${HIVE_HOME}"

test -d "${HIVE_HOME}"

# ========================================
# Cleanup
# ========================================

rm -f "/tmp/apache-hive-${HIVE_VERSION}-bin.tar.gz"

echo "========================================"
echo "Apache Hive installed successfully"
echo "========================================"
