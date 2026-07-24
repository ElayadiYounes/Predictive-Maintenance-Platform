FROM apache/airflow:2.10.2-python3.11

USER root

# ==================================================
# System dependencies
# ==================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    openjdk-17-jdk-headless \
    && rm -rf /var/lib/apt/lists/*

# ==================================================
# Environment variables
# ==================================================
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    SPARK_VERSION=3.5.2 \
    SPARK_HADOOP_PROFILE=3 \
    HADOOP_VERSION=3.3.4 \
    SPARK_HOME=/opt/spark \
    PATH="${SPARK_HOME}/bin:${PATH}"

# ==================================================
# Offline dependencies
# ==================================================
COPY third_party/spark/spark-3.5.2-bin-hadoop3.tgz /tmp/

# ==================================================
# Install Apache Spark
# ==================================================
COPY docker/airflow/scripts/install_spark.sh /tmp/install_spark.sh

RUN chmod +x /tmp/install_spark.sh && \
    /tmp/install_spark.sh && \
    rm /tmp/install_spark.sh

# ==================================================
# Switch to airflow user
# ==================================================
USER airflow

# ==================================================
# Install Python dependencies
# ==================================================
COPY docker/airflow/requirements.txt /tmp/requirements.txt

RUN pip install \
    --no-cache-dir \
    --disable-pip-version-check \
    -r /tmp/requirements.txt