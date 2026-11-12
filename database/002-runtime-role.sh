#!/bin/sh
set -eu
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set ON_ERROR_STOP=1 --set app_password="$CLINTEL_APP_PASSWORD" --set ingest_password="$CLINTEL_INGEST_PASSWORD" --file /runtime-role.sql
