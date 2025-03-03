#!/bin/bash

set -e

echo "Initializing Airflow database..."
airflow db init

echo "Checking if admin user exists..."
if ! airflow users list | awk -F'|' 'NR>2 {print $2}' | tr -d ' ' | grep -qw "admin"; then
    echo "Creating admin user..."
    airflow users create \
        --username admin \
        --password admin \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email dat@workforceoptimizer.com
else
    echo "Admin user already exists."
fi

exec airflow webserver
