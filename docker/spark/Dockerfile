FROM apache/spark:3.5.2


# Switch to root
# ==================================================
USER root


# System dependencies
# ==================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    ca-certificates \
    tini \
    gettext-base \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*


# Environment variables
# ==================================================
ENV SPARK_HOME=/opt/spark \
    HADOOP_AWS_VERSION=3.3.4 \
    AWS_SDK_VERSION=1.12.262 \
    PYTHONUNBUFFERED=1 \
    PYSPARK_PYTHON=python3 \
    PYSPARK_DRIVER_PYTHON=python3 \
    PYTHONPATH=/app \
    PATH="${SPARK_HOME}/bin:${PATH}"


# Install Python dependencies
# ==================================================
COPY docker/spark/requirements.txt /tmp/requirements.txt

RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install \
        --disable-pip-version-check \
        --no-cache-dir \
        -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt


# ==================================================
# Copy third-party dependencies
# ==================================================
COPY third_party/aws/hadoop-aws-3.3.4.jar /tmp/
COPY third_party/aws/aws-java-sdk-bundle-1.12.262.jar /tmp/

# ==================================================
# Install Spark connectors
# ==================================================
COPY docker/spark/scripts/install_connectors.sh /tmp/install_connectors.sh

RUN chmod +x /tmp/install_connectors.sh && \
    /tmp/install_connectors.sh && \
    rm /tmp/install_connectors.sh

# Spark configuration
# ==================================================
COPY docker/spark/conf/spark-defaults.conf /opt/spark/conf/
COPY docker/spark/conf/spark-env.sh /opt/spark/conf/
COPY docker/spark/conf/log4j2.properties /opt/spark/conf/
COPY docker/spark/conf/hive-site.xml /opt/spark/conf/

RUN chmod +x /opt/spark/conf/spark-env.sh && \
    chown -R spark:spark /opt/spark/conf


# Entrypoint
# ==================================================
COPY docker/spark/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh


# Working directory
# ==================================================
WORKDIR /app

RUN mkdir -p /opt/spark/logs && chown -R spark:spark /opt/spark/logs

# Switch back to spark user
# ==================================================
USER spark

ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]

CMD ["bash"]