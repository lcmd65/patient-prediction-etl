from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from minio import Minio

SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS_PATH = "/opt/airflow/dags/credentials.json"
CSV_PATH = "/opt/airflow/dags/data.csv"
BUCKET_NAME = "bronze"

credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
drive_service = build("drive", "v3", credentials=credentials)

minio_client = Minio(
    "minio:9000",
    access_key="admin",
    secret_key="12345678",
    secure=False
)

if not minio_client.bucket_exists(BUCKET_NAME):
    minio_client.make_bucket(BUCKET_NAME)


def download_and_store_file(drive_file_id, file_name):
    request = drive_service.files().get_media(fileId=drive_file_id)
    file_stream = io.BytesIO()

    downloader = MediaIoBaseDownload(file_stream, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

    file_stream.seek(0)
    
    file_size = file_stream.getbuffer().nbytes
    minio_client.put_object(
        BUCKET_NAME, f"bronze/{file_name}", file_stream, length=file_size, part_size=10*1024*1024
    )

    print(f"Uploaded {file_name} to MinIO bucket '{BUCKET_NAME}'.")

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 2, 1),
    'catchup': False
}

dag = DAG(
    'extract',
    default_args=default_args,
    schedule_interval='30 23 * * *', 
)

extract_task = PythonOperator(
    task_id='extract_to_minio',
    python_callable=download_and_store_file,
    op_kwargs = {'drive_file_id': '1xBuBsPr41q1brMbvJLC_O9O_gVVApb-x', 'file_name': 'data.csv'},
    dag=dag
)

extract_task