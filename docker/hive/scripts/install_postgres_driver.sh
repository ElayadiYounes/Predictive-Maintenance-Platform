#!/bin/bash

set -eux

echo "========================================"
echo "Installing PostgreSQL JDBC Driver"
echo "========================================"

# ========================================
# Check required file
# ========================================

test -f "/tmp/postgresql-${POSTGRES_JDBC_VERSION}.jar"

# ========================================
# Remove old PostgreSQL drivers
# ========================================

rm -f "${HIVE_HOME}"/lib/postgresql-*.jar
rm -f "${HIVE_HOME}"/lib/postgresql.jar

# ========================================
# Install PostgreSQL JDBC Driver
# ========================================

cp "/tmp/postgresql-${POSTGRES_JDBC_VERSION}.jar" \
   "${HIVE_HOME}/lib/"

# ========================================
# Create symbolic link
# ========================================

ln -sf \
"${HIVE_HOME}/lib/postgresql-${POSTGRES_JDBC_VERSION}.jar" \
"${HIVE_HOME}/lib/postgresql.jar"

# ========================================
# Cleanup
# ========================================

rm -f "/tmp/postgresql-${POSTGRES_JDBC_VERSION}.jar"

echo "========================================"
echo "PostgreSQL JDBC Driver installed"
echo "========================================"

ls -lh "${HIVE_HOME}"/lib/postgresql*