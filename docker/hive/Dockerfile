FROM eclipse-temurin:17-jre

# ==================================================
# System dependencies
# ==================================================
USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    netcat-openbsd \
    gettext-base \
    procps \
    && rm -rf /var/lib/apt/lists/*

# ==================================================
# Environment Variables
# ==================================================
ENV HIVE_VERSION=3.1.3 \
    HADOOP_VERSION=3.3.4 \
    POSTGRES_JDBC_VERSION=42.7.7 \
    AWS_SDK_VERSION=1.12.262 \
    HIVE_HOME=/opt/hive \
    HADOOP_HOME=/opt/hadoop \
    JAVA_HOME=/opt/java/openjdk \
    PATH="${HIVE_HOME}/bin:${HADOOP_HOME}/bin:${PATH}" \
    HADOOP_CLASSPATH="${HADOOP_HOME}/share/hadoop/tools/lib/*"

# ==================================================
# Third-party dependencies
# ==================================================
COPY third_party/hive/apache-hive-3.1.3-bin.tar.gz /tmp/
COPY third_party/hadoop/hadoop-3.3.4.tar.gz /tmp/
COPY third_party/aws/hadoop-aws-3.3.4.jar /tmp/
COPY third_party/aws/aws-java-sdk-bundle-1.12.262.jar /tmp/
COPY third_party/postgres/postgresql-42.7.7.jar /tmp/

# ==================================================
# Installation scripts
# ==================================================
COPY docker/hive/scripts/install_hive.sh /tmp/
COPY docker/hive/scripts/install_hadoop.sh /tmp/
COPY docker/hive/scripts/install_postgres_driver.sh /tmp/

RUN chmod +x \
        /tmp/install_hive.sh \
        /tmp/install_hadoop.sh \
        /tmp/install_postgres_driver.sh \
    && /tmp/install_hive.sh \
    && /tmp/install_hadoop.sh \
    && /tmp/install_postgres_driver.sh \
    && rm -f \
        /tmp/install_hive.sh \
        /tmp/install_hadoop.sh \
        /tmp/install_postgres_driver.sh \
        /tmp/apache-hive-3.1.3-bin.tar.gz \
        /tmp/hadoop-3.3.4.tar.gz \
        /tmp/hadoop-aws-3.3.4.jar.jar \
        /tmp/aws-java-sdk-bundle-1.12.262.jar  \
        /tmp/postgresql-42.7.7.jar

# ==================================================
# Hive configuration
# ==================================================
COPY docker/hive/conf/ ${HIVE_HOME}/conf/

# ==================================================
# Entrypoint
# ==================================================
COPY docker/hive/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

# ==================================================
# Create non-root user
# ==================================================
RUN useradd -m -u 1005 hive && \
    chown -R hive:hive ${HIVE_HOME}

WORKDIR ${HIVE_HOME}

USER hive

# ==================================================
# Expose Hive Metastore
# ==================================================
EXPOSE 9083

ENTRYPOINT ["/entrypoint.sh"]