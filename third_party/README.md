# Third-Party Dependencies

## Overview

The `third_party` directory contains external software packages required by the OCP Predictive Maintenance Platform.

These dependencies are **not developed within this project**. They are official distributions or libraries used by the platform during container image creation and runtime configuration.

To keep the Git repository lightweight, large binary files (archives and JARs) are excluded from version control. Only the documentation and download utilities are tracked.

---

## Directory Structure

```text
third_party/
├── aws/
├── hadoop/
├── hive/
├── postgres/
├── spark/
├── README.md
├── download.sh
└── download.ps1
```

---

## Dependencies

### Apache Spark

**Version:** 3.5.2

Apache Spark is the distributed processing engine used for large-scale data processing, ETL pipelines, feature engineering, and machine learning workloads.

Expected archive:

```text
spark/spark-3.5.2-bin-hadoop3.tgz
```

Official distribution:

* Apache Spark 3.5.2

---

### Apache Hadoop

**Version:** 3.3.4

Apache Hadoop provides the libraries required by Spark, including filesystem abstractions and compatibility with object storage services.

Expected archive:

```text
hadoop/hadoop-3.3.4.tar.gz
```

Official distribution:

* Apache Hadoop 3.3.4

---

### Apache Hive

**Version:** 3.1.3

Apache Hive provides the metastore service used by Spark SQL to manage databases, tables, schemas, and metadata.

Expected archive:

```text
hive/apache-hive-3.1.3-bin.tar.gz
```

Official distribution:

* Apache Hive 3.1.3

---

### PostgreSQL JDBC Driver

**Version:** 42.7.7

The PostgreSQL JDBC driver enables Java-based applications such as Apache Hive to communicate with the PostgreSQL metadata database.

Expected file:

```text
postgres/postgresql-42.7.7.jar
```

---

### Hadoop AWS Connector

**Version:** 3.3.4

This connector allows Hadoop and Spark to access Amazon S3 compatible object storage services through the `s3a://` filesystem implementation.

Expected file:

```text
aws/hadoop-aws-3.3.4.jar
```

---

### AWS Java SDK Bundle

**Version:** 1.12.262

The AWS SDK bundle provides the implementation required by the Hadoop AWS connector to communicate with S3-compatible object storage systems such as MinIO.

Expected file:

```text
aws/aws-java-sdk-bundle-1.12.262.jar
```

---

## Notes

The versions listed in this directory are selected to ensure compatibility between:

* Apache Spark 3.5.2
* Apache Hadoop 3.3.4
* Apache Hive 3.1.3
* PostgreSQL JDBC Driver 42.7.7
* Hadoop AWS Connector 3.3.4
* AWS Java SDK Bundle 1.12.262

Maintaining compatible versions across these components is essential for reliable execution of the platform's data processing and metadata services.
