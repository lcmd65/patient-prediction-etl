{{ config(
    schema='aio',
    materialized='table'
) }}

SELECT 
    CAST(date AS DATE) AS date,
    CAST(time_block AS INT) AS time_block,
    CAST(bed AS INT) AS bed,
    CAST(total_patient_volume AS FLOAT) AS total_patient_volume
FROM {{ ref('stg_hospital_data') }}
