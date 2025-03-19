import io
import pandas as pd
from minio import Minio


def file_to_parquet(file_stream):
    df = pd.read_csv(file_stream)
    parquet_buffer = io.BytesIO()
    df.to_parquet(parquet_buffer, engine="pyarrow", index=False)
    parquet_buffer.seek(0)

    return parquet_buffer


def store_file(
        minio_client, 
        bucket_name, 
        folder, 
        parquet_buffer, 
        content_type):
    minio_client.put_object(
        bucket_name,
        folder,
        data=parquet_buffer,
        length=parquet_buffer.getbuffer().nbytes,
        content_type = content_type
    )
