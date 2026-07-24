#!/bin/bash

# ==================================================
# Java
# ==================================================
export JAVA_HOME=/opt/java/openjdk

# ==================================================
# Spark
# ==================================================
export SPARK_HOME=/opt/spark

export PYSPARK_PYTHON=python3
export PYSPARK_DRIVER_PYTHON=python3

export SPARK_MASTER_HOST=${SPARK_MASTER_HOST:-spark-master}
export SPARK_MASTER_PORT=${SPARK_MASTER_PORT:-7077}