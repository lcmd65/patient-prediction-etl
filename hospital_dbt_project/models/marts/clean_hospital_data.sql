{{ config(
    schema='aio',
    materialized='table',
    alias='clean_hospital_data'
) }}

WITH base_data AS (
    SELECT 
        date,
        time_block,
        bed,
        total_patient_volume,
        ((date - DATE '2021-01-01') / 42)::INT AS cycle_id
    FROM {{ ref('stg_hospital_data') }}
),
filtered_data AS (
    SELECT *
    FROM base_data
    WHERE date >= DATE '2021-01-01' + (cycle_id * 42) + 14
)
SELECT *
FROM filtered_data
