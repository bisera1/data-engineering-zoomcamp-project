# Getting Started

To get started with the project, follow these steps:

### Prerequisites
Before you begin, make sure you have the following installed:

Docker: Used to containerize and run Airflow and PySpark.

Docker Compose: Helps manage multi-container Docker applications.

### Step 1: Clone the Repository
First, clone the repository:

```bash
git clone <repository-url>
cd <repository-name>
```


### Step 2: Navigate to the Project Directory
Navigate to the directory where the docker-compose.yml file is located. This file will set up the Airflow environment with PySpark installed inside.

### Step 3: Start Docker Containers
Run the following command to start the Airflow and PySpark containers in detached mode. This will set up the environment with all necessary dependencies.

```bash
docker-compose up -d
```

This command will:

Start the Airflow web server and scheduler.

Initialize PySpark inside the Airflow environment.

Create necessary volumes and networks for your containers.

### Step 4: Initialize the Database
Once the containers are running, you need to create the required tables in the PostgreSQL database. Run the script provided for this purpose.

Script to Create Tables: You can execute the script that sets up the necessary database schema (tables) in PostgreSQL. The script will automatically create the final table where the transformed data will be loaded.


### Step 5: Access the Airflow UI
To manage and monitor your DAGs, you’ll need to access the Airflow UI.

Open your browser and navigate to http://localhost:8080.

Log in using the credentials  (airflow airflow).

### Step 6: Trigger the DAGs
Once you're inside the Airflow UI, you can trigger the two DAGs (Directed Acyclic Graphs) that manage the ETL pipeline.

After the DAGs have run successfully, you can check the Pgadmin to verify that the data has been loaded properly.


# Project Overview

This project implements a simple ETL (Extract, Transform, Load) pipeline for a data engineering use case, using Apache Airflow for orchestration, PySpark for data processing, and metabase for data visualization. The goal of this project is to fetch job posting data from two job listing APIs (jobicy.com and remoteok.com), process and clean the data, and then load it into a database for further analysis and visualization.

The project follows the following steps:

Data Extraction (Extract): Data is fetched from two APIs (jobicy.com and remoteok.com).

Data Transformation (Transform): The fetched data is processed using PySpark to ensure consistency and structure.

Data Loading (Load): The new data is ingested into a database, which serves as the source for reporting and analysis.

Visualization: Metabase connects to the database to provide insights and analysis of the data.



## Data Sources

The project works with two primary data sources:

Jobicy API: This API provides job postings from various companies offering remote positions.

RemoteOK API: This API also offers remote job listings.

Both data sources provide similar job data, including job title, company name, job description, and location.


## ETL Workflow
1. Extract (Data Collection)
The first task in the Airflow DAG is to fetch the data from the two job APIs (jobicy.com and remoteok.com). The data is retrieved in JSON format and stored as a CSV file. This step serves as the extraction phase of the ETL process.

Airflow Task: Two daily scheduled Airflow task fetches data from the APIs and stores the raw JSON data in CSV files.

Data Storage: The raw data is temporarily saved as CSV files before further processing.

2. Transform (Data Processing)
Once the data is collected, the next step is to process it using PySpark, the transformation step involves cleaning and structuring the data to ensure uniformity and accuracy across both datasets.

Data Transformation: The data is transformed into a consistent schema suitable for database ingestion.

New Data Filtering: To ensure that only new records are ingested into the database, the PySpark processing logic compares the fetched data with the existing records in the database and only processes the new data.

3. Load (Data Ingestion)
Once the data is processed, it is ingested into the database. Both job sources are stored in a single table in the database.

**Database**: The processed data is inserted into a relational database PostgreSQL.

The database is connected with Metabase which is used for creating visualisations. the visualisation are stored in the visualisations-metabase folder with the queries used to build them.



