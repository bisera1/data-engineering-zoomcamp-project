from pyspark.sql import SparkSession
from airflow.operators.python import PythonOperator
from airflow import DAG
from datetime import datetime
from pyspark.sql.functions import col, to_date
from pyspark.sql.functions import col, regexp_replace, lower, trim
from pyspark.sql import functions as F
import os
import requests
import pandas as pd

dag = DAG(
    'remoteok_dag',
    description='Airflow job to fetch the data from api and process it',
    schedule_interval='@daily',
    start_date=datetime(2025, 3, 31),
    catchup=False
)

today_date = datetime.now().strftime('%Y-%m-%d')

data_folder_path = '/opt/airflow/jobs/'
data_file_path = os.path.join(data_folder_path, f'data_remoteok_{today_date}.csv')


def api_data():
    url = "https://remoteok.com/api?"
    headers = {"User-Agent": "myApp/1.0"}

    jobs_list = []

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        jobs = response.json()

        for job in jobs[1:]:
            job_data = {
                "id": job.get("id"),
                "position_title": job.get("position"),
                "date_posted": job.get("date"),
                "company": job.get("company"),
                "location": job.get("location"),
                "tags": job.get("tags"),
                "salary_min": job.get("salary_min"),
                "salary_max": job.get("salary_max")
            }
            jobs_list.append(job_data)

        df = pd.DataFrame(jobs_list)
        df.to_csv(data_file_path, index=False)

    except Exception as e:
        print(f"Error: {e}")


api_data_task = PythonOperator(
    task_id='api_data',
    python_callable=api_data,
    dag=dag
)


def run_spark_job():
    if os.path.exists(data_folder_path) and os.path.isfile(data_file_path):
        print("EXISTS")
        spark = SparkSession.builder \
            .appName("PySpark Example") \
            .config("spark.jars", "/opt/airflow/jobs/postgresql-42.7.5.jar") \
            .getOrCreate()
        df = spark.read.option("header", "true").csv(data_file_path)

        df = df.withColumnRenamed("position_title", "job_title")
        df = df.withColumnRenamed("tags", "job_industry")

        df = df.withColumn("job_title", lower(col("job_title")))
        df = df.withColumn("date_posted_timestamp", F.to_timestamp(F.col("date_posted"), "yyyy-MM-dd'T'HH:mm:ssXXX"))
        df = df.withColumn("date_posted",F.to_date(F.col("date_posted_timestamp")))
        df = df.drop("date_posted_timestamp")
        df = df.withColumn("location", lower(col("location")))
        df = df.withColumn("salary_min", col("salary_min").cast("double"))
        df = df.withColumn("salary_max", col("salary_max").cast("double"))
        df = df.withColumn("job_industry", lower(regexp_replace(trim(col("job_industry")), "&", "&amp;")))
        df = df.withColumn("job_industry", regexp_replace(col("job_industry"), "[\\[\\]']+", ""))
        df = df.withColumn(
            'level',
            F.when(F.lower(F.col('job_title')).contains('junior'), 'junior')
            .when(F.lower(F.col('job_title')).contains('intern'), 'intern')
            .when(F.lower(F.col('job_title')).contains('internship'), 'intern')
            .when(F.lower(F.col('job_title')).contains('senior'), 'senior')
            .when(F.lower(F.col('job_title')).contains('lead'), 'lead')
            .when(F.lower(F.col('job_title')).contains('manager'), 'manager')
            .when(F.lower(F.col('job_title')).contains('director'), 'director')
            .when(F.lower(F.col('job_title')).contains('chief'), 'c-level')
            .when(F.lower(F.col('job_title')).contains('board member'), 'board member')
            .otherwise('unknown'))
        df = df.withColumn("average_salary", (F.col("salary_min") + F.col("salary_max")) / 2)
        df = df.withColumn('remote', F.when(F.lower(F.col('location')).contains('remote'), 'yes').otherwise('no') )

        url = 'jdbc:postgresql://postgres:5432/airflow'

        existing_df = spark.read.format("jdbc")\
            .option("driver", "org.postgresql.Driver") \
            .option("url", url) \
            .option("dbtable", "jobs.jobs_table") \
            .option("user", "postgres") \
            .option("password", "airflow").load()

        new_records_df = df.join(existing_df, df.id == existing_df.id, "left_anti")

        new_records_df.write.format("jdbc").mode("append") \
            .option("driver", "org.postgresql.Driver") \
            .option("url", url) \
            .option("dbtable", "jobs.jobs_table") \
            .option("user", "postgres") \
            .option("password", "airflow").save()

    else:
        raise FileNotFoundError(f"Either the folder {data_folder_path} or the file {data_file_path} does not exist!")


spark_python_task = PythonOperator(
    task_id='run_spark_job',
    python_callable=run_spark_job,
    dag=dag
)
api_data_task >> spark_python_task
