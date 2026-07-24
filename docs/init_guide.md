# Project Initialization Guide

## Purpose

This guide explains the steps required to initialize the OCP Predictive Maintenance Platform after cloning the repository.

It is intended for developers who want to set up a complete development environment from scratch.

---

# Prerequisites

Before starting, make sure the following software is installed on your machine:

* Git
* Docker Engine
* Docker Compose
* Bash (Linux/macOS) or PowerShell (Windows)

Verify the installation:

```bash
git --version
docker --version
docker compose version
```

---

# Step 1 — Clone the Repository

Clone the project from the remote repository.

```bash
git clone <repository-url>
cd ocp-predictive-maintenance-platform
```

---

# Step 2 — Configure the Environment

Create your local environment file from the provided template.

Linux/macOS

```bash
cp .env.example .env.dev
```

Windows PowerShell

```powershell
Copy-Item .env.example .env.dev
```

Update the values in `.env.dev` according to your local environment.

Examples include:

* Database credentials
* MinIO credentials
* Airflow administrator account
* SMTP configuration

---

# Step 3 — Download Third-Party Dependencies

Download all external software required to build the Docker images.

Linux/macOS

```bash
./third_party/download.sh
```

Windows PowerShell

```powershell
.\third_party\download.ps1
```

This step downloads the required Apache Spark, Apache Hadoop, Apache Hive, PostgreSQL JDBC, and AWS connector packages into the `third_party` directory.

---

# Step 4 — Build Docker Images

Build every custom Docker image defined by the project.

Development environment

```bash
 docker compose --env-file .env.dev -f docker-compose.dev.yml build 
```

Production environment

```bash
docker compose -f docker-compose.prod.yml build
```

Depending on your machine and internet connection, this step may take several minutes.

---

# Step 5 — Start the Platform

Launch all platform services.

Development

```bash
 docker compose --env-file .env.dev -f docker-compose.dev.yml up -d
```

Production

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d
```

Docker will create the required containers, volumes, and network automatically.

---

# Step 6 — Verify the Deployment

Check that every service is running correctly.

```bash
docker ps
```

The platform should start the required infrastructure services, including:

* MinIO
* PostgreSQL
* Apache Hive Metastore
* Apache Spark
* Apache Airflow
* API
* Machine Learning service

If necessary, inspect the logs of a specific service.

Example:

```bash
docker compose -f docker-compose.dev.yml logs spark-master
```

---

# Step 7 — Stop the Platform

To stop all running services:

Development

```bash
docker compose -f docker-compose.dev.yml down
```

Production

```bash
docker compose -f docker-compose.prod.yml down
```

---

# Additional Documentation

For more information, refer to the project documentation:

* `README.md`
* `docs/`
* `third_party/README.md`

These documents describe the project architecture, dependencies, and development workflow in greater detail.
