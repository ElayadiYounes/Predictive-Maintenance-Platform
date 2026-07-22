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
ENV HIVE_VERSION=4.0.1 \
    POSTGRES_JDBC_VERSION=42.7.7 \
    HIVE_HOME=/opt/hive \
    JAVA_HOME=/opt/java/openjdk \
    PATH="${HIVE_HOME}/bin:${PATH}"

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
    chown -R hive:hive ${HIVE_HOME} \

WORKDIR ${HIVE_HOME}

USER hive

# ==================================================
# Expose Hive Metastore
# ==================================================
EXPOSE 9083

ENTRYPOINT ["/entrypoint.sh"]