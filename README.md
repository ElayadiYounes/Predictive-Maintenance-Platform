# Predictive Maintenance Platform

## Overview

Predictive Maintenance Platform is an end-to-end Data Engineering platform designed to support predictive maintenance in industrial environments. The project aims to collect, process, analyze, and visualize equipment data in order to detect abnormal behavior, estimate equipment health, and assist maintenance teams in making informed decisions.

Developed as part of an internship project, the platform focuses on conveyor monitoring using historical industrial data. Although the current implementation targets conveyor systems, the architecture is designed to be extensible to other industrial equipment in the future.

## Objectives

The platform aims to:

* Build a modern Data Engineering pipeline based on the Medallion Architecture (Bronze, Silver, Gold).
* Automate data ingestion, transformation, and orchestration.
* Detect anomalies and predict potential equipment failures using Machine Learning.
* Provide maintenance indicators and decision-support dashboards.
* Generate maintenance alerts and analytical reports.
* Offer a modular and scalable architecture that can evolve with future industrial needs.

## Main Technologies

* Python
* Apache Spark (PySpark)
* Apache Hive
* Apache Airflow
* MinIO (Data Lake)
* FastAPI
* XGBoost
* Isolation Forest
* Docker
* Metabase

## Project Status

🚧 This project is currently under active development.

The first version focuses on the implementation of the core data pipeline, predictive models, and visualization components. Additional features and improvements will be integrated progressively throughout the project.

## License

This repository is intended for educational and research purposes. Industrial data and company-specific information are not included in this repository.
