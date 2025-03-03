from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
import psycopg2
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from airflow.operators.bash import BashOperator
import os
import io

SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS_PATH = "/opt/airflow/dags/credentials.json"
CSV_PATH = "/opt/airflow/dags/data.csv"

def download_csv_from_gdrive(file_id):
    creds = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
    service = build("drive", "v3", credentials=creds)

    request = service.files().get_media(fileId=file_id)
    file = io.BytesIO()
    downloader = MediaIoBaseDownload(file, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%")

    file.seek(0)
    df = pd.read_csv(file)
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
    'gdrive_to_postgres',
    default_args=default_args,
    schedule_interval = '0 23 * * *',
    catchup = False
)

download_task = PythonOperator(
    task_id='extract',
    python_callable=download_csv_from_gdrive,
    op_kwargs = {'file_id': '1xBuBsPr41q1brMbvJLC_O9O_gVVApb-x'},
    dag=dag
)

load_task = PythonOperator(
    task_id='transform',
    python_callable = load_data_to_postgres,
    dag=dag
)


run_dbt_staging = BashOperator(
    task_id='run_dbt_staging',
    bash_command="docker exec dbt dbt run --profiles-dir /root/.dbt --select stg_hospital_data",
    dag=dag
)

run_dbt_clean = BashOperator(
    task_id='run_dbt_clean',
    bash_command="docker exec dbt dbt run --profiles-dir /root/.dbt --select clean_hospital_data",
    dag=dag
)

download_task >> load_task >> run_dbt_staging >> run_dbt_clean