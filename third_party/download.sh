#!/usr/bin/env bash

set -e

echo "==========================================="
echo "Downloading Third Party Dependencies"
echo "==========================================="

mkdir -p aws
mkdir -p postgres
mkdir -p spark
mkdir -p hive
mkdir -p hadoop

echo ""
echo "Downloading Spark..."

curl -L -k \
https://archive.apache.org/dist/spark/spark-3.5.2/spark-3.5.2-bin-hadoop3.tgz \
-o spark/spark-3.5.2-bin-hadoop3.tgz

echo ""
echo "Downloading Hadoop..."

curl -L -k \
https://archive.apache.org/dist/hadoop/common/hadoop-3.3.4/hadoop-3.3.4.tar.gz \
-o hadoop/hadoop-3.3.4.tar.gz

echo ""
echo "Downloading Hive..."

curl -L -k \
https://archive.apache.org/dist/hive/hive-3.1.3/apache-hive-3.1.3-bin.tar.gz \
-o hive/apache-hive-3.1.3-bin.tar.gz

echo ""
echo "Downloading PostgreSQL JDBC Driver..."

curl -L -k \
https://jdbc.postgresql.org/download/postgresql-42.7.7.jar \
-o postgres/postgresql-42.7.7.jar

echo ""
echo "Downloading Hadoop AWS..."

curl -L -k \
https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar \
-o aws/hadoop-aws-3.3.4.jar

echo ""
echo "Downloading AWS SDK Bundle..."

curl -L -k \
https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar \
-o aws/aws-java-sdk-bundle-1.12.262.jar

echo ""
echo "Done."