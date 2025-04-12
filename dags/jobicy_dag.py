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
    'jobcy_dag',
    description='Airflow job to fetch the data from api and process it',
    schedule_interval='@daily',
    start_date=datetime(2025, 3, 31),
    catchup=False
)

today_date = datetime.now().strftime('%Y-%m-%d')

data_folder_path = '/opt/airflow/jobs/'
data_file_path = os.path.join(data_folder_path, f'data_jobcy_{today_date}.csv')


def api_data():
    url = "https://jobicy.com/api/v2/remote-jobs"
    headers = {"User-Agent": "myApp/1.0"}

    jobs_list = []

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        jobs = response.json()

        for job in jobs.get('jobs'):
            job_data = {
                "id": job.get("id"),
                "jobTitle": job.get("jobTitle"),
                "pubDate": job.get("pubDate"),
                "companyName": job.get("companyName"),
                "jobGeo": job.get("jobGeo"),
                "jobIndustry": job.get("jobIndustry"),
                "annualSalaryMin": job.get("annualSalaryMin"),
                "annualSalaryMax": job.get("annualSalaryMax")
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

        df = df.withColumnRenamed("jobTitle", "job_title")
        df = df.withColumnRenamed("jobGeo", "location")
        df = df.withColumnRenamed("companyName", "company")
        df = df.withColumnRenamed("annualSalaryMin", "salary_min")
        df = df.withColumnRenamed("annualSalaryMax", "salary_max")
        df = df.withColumnRenamed("jobIndustry", "job_industry")
        df = df.withColumnRenamed("pubDate", "date_posted")


        df = df.withColumn("job_title", lower(col("job_title")))
        df = df.withColumn("pubDate_timestamp", F.to_timestamp(F.col("date_posted"), "yyyy-MM-dd'T'HH:mm:ssXXX"))
        df = df.withColumn("date_posted",F.to_date(F.col("date_posted")))
        df = df.drop("pubDate_timestamp")
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

        existing_df = spark.read.format("jdbc") \
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
