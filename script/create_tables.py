import psycopg2

conn = psycopg2.connect(
        host="localhost",
        database="airflow",
        user="postgres",
        password="airflow"
    )
cursor = conn.cursor()

try:

    create_schema_query = """
        CREATE SCHEMA IF NOT EXISTS jobs;
        """
    cursor.execute(create_schema_query)

    create_table_query_remote = """
    CREATE TABLE IF NOT EXISTS jobs.jobs_table (
        id TEXT  PRIMARY KEY,
        date_posted DATE,
        salary_min DOUBLE PRECISION,
        average_salary DOUBLE PRECISION,
        salary_max DOUBLE PRECISION,
        job_industry TEXT,
        level TEXT NOT NULL,
        remote TEXT NOT NULL,
        job_title TEXT,
        company TEXT,
        location TEXT
    );
    """

    cursor.execute(create_table_query_remote)

    conn.commit()

    print("Tables are created successfully.")

except Exception as error:
    print(f"Error creating table: {error}")
finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()
