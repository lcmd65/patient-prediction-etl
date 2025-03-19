from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
import psycopg2
from airflow.operators.bash import BashOperator
import os
import io
from minio import Minio

BUCKET_NAME = "bronze"
CSV_PATH = "/opt/airflow/dags/hospital_data.csv"

minio_client = Minio(
    "localhost:9000",
    access_key="admin",
    secret_key="12345678",
    secure=False
)


def download_parquet_from_minio(PARQUET_FILE):
    response = minio_client.get_object(BUCKET_NAME, PARQUET_FILE)
    file_data = io.BytesIO(response.read())
    df = pd.read_parquet(file_data, engine="pyarrow")

    file_data.seek(0)
    df = pd.read_csv(file_data)
    df.to_csv(CSV_PATH, index=False)
    print(f"File downloaded successfully to {CSV_PATH}")

def load_data_to_postgres():
        conn = psycopg2.connect(
            host = "postgres",
            database = "hospital",
            user = "admin",
            password = "123456",
            port = 5432
        )
        cursor = conn.cursor()

        df = pd.read_csv(CSV_PATH)
        for _, row in df.iterrows():
            cursor.execute(
                "INSERT INTO aio.raw_hospital_data (date, time_block, bed, total_patient_volume) VALUES (%s, %s, %s, %s)",
                (row["date"], row["time_block"], row["bed"], row["total_patient_volume"])
            )

        conn.commit()
        cursor.close()
        conn.close()
        print("Data loaded successfully!")

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 2, 1)
}

dag = DAG(
    'transform',
    default_args=default_args,
    schedule_interval = '0 23 * * *',
    catchup = False
)

download_task = PythonOperator(
    task_id='extract_minio',
    python_callable=download_parquet_from_minio,
    op_kwargs = {'PARQUET_FILE': 'hospital_data.parquet'},
    dag=dag
)

load_task = PythonOperator(
    task_id='transform',
    python_callable = load_data_to_postgres,
    dag=dag
)

run_dbt_staging = BashOperator(
    task_id='dbt_staging',
    bash_command="docker exec dbt dbt run --profiles-dir /root/.dbt --select stg_hospital_data",
    dag=dag
)

run_dbt_clean = BashOperator(
    task_id='dbt_clean',
    bash_command="docker exec dbt dbt run --profiles-dir /root/.dbt --select clean_hospital_data",
    dag=dag
)

download_task >> load_task >> run_dbt_staging >> run_dbt_clean