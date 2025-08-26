#!/bin/bash
# set -e

# echo "Running db prep..."

# psql "postgres://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST/$POSTGRES_DB?sslmode=disable" <<-EOSQL
# -- YOUR SQL Statements here
# EOSQL
# psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d "$POSTGRES_DB"  <<-EOSQL
#      create schema if not exists $SCHEMA;
#      create table $SCHEMA.todos (
#         id serial primary key,
#         done boolean not null default false,
#         task text not null,
#         due timestamptz
#      );
#      create role $ANON nologin;
#      create role $AUTHENTICATOR noinherit login password '$POSTGRES_PASSWORD';
#      grant $ANON to $AUTHENTICATOR;
# EOSQL


# psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
#     CREATE SCHEMA IF NOT EXISTS public;
#     -- other SQL statements here...
# EOSQL
