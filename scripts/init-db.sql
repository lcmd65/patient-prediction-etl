CREATE SCHEMA IF NOT EXISTS aio;

CREATE TABLE IF NOT EXISTS aio.raw_hospital_data (
    id SERIAL PRIMARY KEY,
    date DATE,
    time_block INT,
    bed INT,
    total_patient_volume FLOAT
);

CREATE TABLE IF NOT EXISTS aio.clean_hospital_data (
    id SERIAL PRIMARY KEY,
    date DATE,
    time_block INT,
    bed INT,
    total_patient_volume FLOAT,
    cycle_id INT
);


