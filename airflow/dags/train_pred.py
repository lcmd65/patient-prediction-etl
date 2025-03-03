from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import requests
import pandas as pd
from sqlalchemy import create_engine

DB_CONNECTION_STRING = "postgresql://user:password@db_host:5432/db_name"
TRAIN_API_URL = "http://your-flask-server:5000/train"
PREDICT_API_URL = "http://your-flask-server:5000/predict"

def fetch_today_data():
    engine = create_engine(DB_CONNECTION_STRING)

    today = datetime.now().date()
    
    query = f"""
    SELECT date, time_block, bed, total_patient_volume
    FROM aio.filtered_data
    WHERE date = '{today}'
    """
    df = pd.read_sql(query, engine)

    if df.empty:
        raise Exception(f"No data found for today ({today}) in aio.filtered_data!")

    return df

def split_train_predict():
    df = fetch_today_data()
    df = df.sort_values(by="time_block").reset_index(drop=True)
    train_size = int(len(df) * 0.7)
    train_df = df.iloc[:train_size]
    predict_df = df.iloc[train_size:]

    return train_df, predict_df

def train_model():
    train_df, _ = split_train_predict()
    request_data = train_df.to_dict(orient="records")

    response = requests.post(TRAIN_API_URL, json=request_data)

    if response.status_code == 200:
        print("Training completed successfully!")
    else:
        raise Exception(f"Training API failed: {response.status_code} - {response.text}")

def predict():
    _, predict_df = split_train_predict()
    request_data = predict_df.to_dict(orient="records")

    response = requests.post(PREDICT_API_URL, json=request_data)

    if response.status_code == 200:
        predictions = response.json().get("forecast", [])

        forecast_df = pd.DataFrame(predictions)

        engine = create_engine(DB_CONNECTION_STRING)
        forecast_df.to_sql("aio.prediction_results", engine, if_exists="replace", index=False)

        print("Predictions saved to database!")

    else:
        raise Exception(f"Prediction API failed: {response.status_code} - {response.text}")

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 2, 1),
    'catchup': False
}

dag = DAG(
    'train_and_predict_patient_volume',
    default_args=default_args,
    schedule_interval='30 23 * * *', 
)

train_task = PythonOperator(
    task_id='train_model',
    python_callable=train_model,
    dag=dag
)

predict_task = PythonOperator(
    task_id='predict',
    python_callable=predict,
    dag=dag
)

train_task >> predict_task
