FROM eclipse-temurin:8-jre-focal

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
    HADOOP_CLASSPATH="${HADOOP_HOME}/share/hadoop/tools/lib/*"
# Global PATH
ENV PATH="${HIVE_HOME}/bin:${HADOOP_HOME}/bin:${JAVA_HOME}/bin:${PATH}"

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
# SÉCURITÉ : WRAPPER JAVA (Bloque le JDWP forcé par l'hôte)
# ==================================================
RUN mv /opt/java/openjdk/bin/java /opt/java/openjdk/bin/java.real && \
    echo '#!/bin/bash' > /opt/java/openjdk/bin/java && \
    echo 'unset JAVA_TOOL_OPTIONS _JAVA_OPTIONS' >> /opt/java/openjdk/bin/java && \
    echo 'NEW_ARGS=()' >> /opt/java/openjdk/bin/java && \
    echo 'for arg in "$@"; do' >> /opt/java/openjdk/bin/java && \
    echo '    if [[ "$arg" != *"jdwp"* && "$arg" != *"Xrunjdwp"* ]]; then' >> /opt/java/openjdk/bin/java && \
    echo '        NEW_ARGS+=("$arg")' >> /opt/java/openjdk/bin/java && \
    echo '    fi' >> /opt/java/openjdk/bin/java && \
    echo 'done' >> /opt/java/openjdk/bin/java && \
    echo 'exec /opt/java/openjdk/bin/java.real "${NEW_ARGS[@]}"' >> /opt/java/openjdk/bin/java && \
    chmod +x /opt/java/openjdk/bin/java


# ==================================================
# Create non-root user
# ==================================================
RUN useradd -m -u 1005 -s /bin/bash hive && \
    echo 'unset JAVA_TOOL_OPTIONS _JAVA_OPTIONS' > /home/hive/.bashrc && \
    echo 'export JAVA_TOOL_OPTIONS="" _JAVA_OPTIONS="" HIVE_OPTS=""' >> /home/hive/.bashrc && \
    echo "export HIVE_HOME=/opt/hive" >> /home/hive/.bashrc && \
    echo "export HADOOP_HOME=/opt/hadoop" >> /home/hive/.bashrc && \
    echo "export JAVA_HOME=/opt/java/openjdk" >> /home/hive/.bashrc && \
    echo 'export HADOOP_CLASSPATH=$HADOOP_HOME/share/hadoop/tools/lib/*' >> /home/hive/.bashrc && \
    echo 'export PATH=$HIVE_HOME/bin:$HADOOP_HOME/bin:$JAVA_HOME/bin:$PATH' >> /home/hive/.bashrc && \
    mkdir -p /tmp/hive && \
    chown -R hive:hive /home/hive ${HIVE_HOME} /tmp/hive && \
    chmod 1777 /tmp /tmp/hive




# ==================================================
# Working directory
# ==================================================
WORKDIR ${HIVE_HOME}


# ==================================================
# Runtime user
# ==================================================
USER hive

# ==================================================
# Expose Hive Metastore
# ==================================================
EXPOSE 9083

ENTRYPOINT ["/entrypoint.sh"]