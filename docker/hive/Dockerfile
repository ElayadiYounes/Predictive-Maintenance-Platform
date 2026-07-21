FROM eclipse-temurin:17-jre

# ==================================================
# System dependencies
# ==================================================
USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    bash \
    netcat-openbsd \
    procps \
    && rm -rf /var/lib/apt/lists/*

# ==================================================
# Environment Variables
# ==================================================
ENV HIVE_VERSION=4.0.1 \
    POSTGRES_JDBC_VERSION=42.7.7 \
    HIVE_HOME=/opt/hive \
    JAVA_HOME=/opt/java/openjdk \
    HADOOP_HOME=/opt/hadoop \
    PATH="${PATH}:/opt/hive/bin"

# ==================================================
# Installation scripts
# ==================================================
COPY docker/hive/scripts/install_hive.sh /tmp/
COPY docker/hive/scripts/install_postgres_driver.sh /tmp/

RUN chmod +x \
        /tmp/install_hive.sh \
        /tmp/install_postgres_driver.sh \
    && /tmp/install_hive.sh \
    && /tmp/install_postgres_driver.sh \
    && rm -f \
        /tmp/install_hive.sh \
        /tmp/install_postgres_driver.sh

# ==================================================
# Hive configuration
# ==================================================
COPY docker/hive/conf/hive-site.xml ${HIVE_HOME}/conf/

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

USER hive

# ==================================================
# Expose Hive Metastore
# ==================================================
EXPOSE 9083

ENTRYPOINT ["/entrypoint.sh"]