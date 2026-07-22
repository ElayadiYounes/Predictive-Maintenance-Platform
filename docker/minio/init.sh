#!/bin/sh

set -e

echo "==========================================="
echo "OCP Predictive Maintenance Platform"
echo "MinIO Bootstrap"
echo "==========================================="

echo "Waiting for MinIO..."

until mc alias set local \
    http://minio:${MINIO_API_PORT} \
    "${MINIO_ROOT_USER}" \
    "${MINIO_ROOT_PASSWORD}" >/dev/null 2>&1
do
    sleep 2
done

echo "MinIO is ready."

create_bucket() {

    BUCKET=$1

    if mc ls local/"${BUCKET}" >/dev/null 2>&1
    then
        echo "Bucket '${BUCKET}' already exists."
    else
        echo "Creating bucket '${BUCKET}'..."

        mc mb local/"${BUCKET}"

        echo "Bucket '${BUCKET}' created."
    fi
}

echo
echo "Creating Data Lake buckets..."

create_bucket "${BRONZE_BUCKET}"
create_bucket "${SILVER_BUCKET}"
create_bucket "${GOLD_BUCKET}"
create_bucket "${MODELS_BUCKET}"

echo
echo "==========================================="
echo "MinIO bootstrap completed successfully."
echo "==========================================="