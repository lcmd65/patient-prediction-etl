{{ config(
    schema='aio',
    materialized='view'
) }}

WITH source AS (
    SELECT 
        date,
        time_block,
        bed,
        total_patient_volume
    FROM {{ source('hospital', 'raw_hospital_data') }}
)

SELECT * FROM source
