@echo off
setlocal

:: Set DB credentials from command line arguments
set DB_PASSWORD=%1
set DB_NAME=%2

:: check if user has Chocolatey installed
where choco >nul 2>nul
if %errorlevel% neq 0 (
    echo Please install Chocolatey first!
    echo You can do this by running this command:
    echo @"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"
    echo.
    echo After that open new cmd window and run setup.py again

    exit /b 1
)
:: Install PostgreSQL using Chocolatey
choco install postgresql

:: Refresh environment to get access to initdb and psql commands
call RefreshEnv.cmd

:: Initialize the database cluster
initdb --locale=C.UTF-8 --encoding=UTF8 -D "C:\Program Files\PostgreSQL\data"

:: Find version of PostgreSQL
for /f "tokens=3 delims= " %%v in ('psql -V') do (
    for /f "tokens=1 delims=." %%m in (%%v) do set PG_VER=%%m
)

:: Start the PostgreSQL service
echo Starting service: postgresql-x64-%PG_VER%
net start postgresql-x64-%PG_VER%


echo Check generated default password for postgres user above
echo It'll look like that:
echo WARNING: Generated password: ...
echo Use it below

:loop1
:: Set a password on default postgres user and create a new database
psql -U postgres -c "ALTER ROLE postgres WITH PASSWORD '%DB_PASSWORD%';"
if %errorlevel% neq 0 (
    echo Wrong password. Please try again.
    goto loop1
)

set PGPASSWORD=%DB_PASSWORD%
psql -U postgres -c "CREATE DATABASE %DB_NAME% OWNER postgres;"

:: Run the script to create the tables and relationships
psql -U postgres -d %DB_NAME% -f scripts/script.sql

set PGPASSWORD=
endlocal
