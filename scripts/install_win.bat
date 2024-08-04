@echo off
setlocal

:: Set DB credentials from command line arguments
set DB_PASSWORD=%1
set DB_NAME=%2

:: Check if Chocolatey is installed
where choco >nul 2>nul
if %errorlevel% neq 0 (
    echo Installing Chocolatey...
    @"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"
)

:: Install PostgreSQL using Chocolatey
choco install postgresql

:: Find the path to initdb and psql
for /f "delims=" %%i in ('where initdb') do set INITDB_PATH=%%i
for /f "delims=" %%i in ('where psql') do set PSQL_PATH=%%i

:: Initialize the database cluster
"%INITDB_PATH%" --locale=C.UTF-8 --encoding=UTF8 -D "C:\Program Files\PostgreSQL\data"

:: Find and start the PostgreSQL service
for /f "tokens=*" %%s in ('sc query state^= all ^| findstr /I "postgresql"') do (
    echo Starting service: %%s
    net start %%s
)

:: Set a password on default postgres user and create a new database
"%PSQL_PATH%" -U postgres -c "ALTER ROLE postgres WITH PASSWORD '%DB_PASSWORD%';"
"%PSQL_PATH%" -U postgres -c "CREATE DATABASE %DB_NAME% OWNER postgres;"

:: Run the script to create the tables and relationships
"%PSQL_PATH%" -U postgres -d %DB_NAME% -f script.sql

endlocal
