#!/bin/bash

# Set DB credentials from environment variables
DB_PASSWORD=${DB_PASSWORD:-0}
DB_NAME=${DB_NAME:-TMLSchat}
PM=${PM:-pacman -S}

# Install PostgreSQL
sudo $PM postgresql

# Initialize the database cluster
sudo su -l postgres -c "initdb --locale=C.UTF-8 --encoding=UTF8 -D '/var/lib/postgres/data'"

# Start the PostgreSQL service
sudo systemctl enable postgresql
sudo systemctl start postgresql &&

# Set a password on default postgres user and create a new database

sudo -u postgres psql -c "ALTER ROLE postgres WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER postgres;"

# Run the script to create the tables and relationships
psql -U postgres -d $DB_NAME -f script.sql