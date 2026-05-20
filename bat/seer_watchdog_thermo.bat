@echo off
set sourceDir=%1

:: Check if the source directory argument is provided
if "%~1" == "" (
    echo You must provide the *.raw file path.
    exit /B -1
)

set watchdog_batch_script_log=C:\seer-scripts\watchdog3\script_logs
echo %DATE% %TIME% - Invoked with Thermo Raw File: %sourceDir% >> %watchdog_batch_script_log%

:: Extract the filename from the full path
for %%I in (%sourceDir%) do set fileName=%%~nxI

:: Initialize variables
set aws_region=
set bucket_name=
set env_access_key_var=
set env_secret_key_var=

:: Determine which environment-backed AWS credentials and bucket to use based on the filename
if not "%fileName:EXP=%"=="%fileName%" (
    :: EXP detected
    set aws_region=us-west-2
    set bucket_name=seer-internalms
    set env_access_key_var=SEER_AWS_ACCESS_KEY_ID_US
    set env_secret_key_var=SEER_AWS_SECRET_ACCESS_KEY_US
) else if not "%fileName:USTESTING=%"=="%fileName%" (
    :: USTESTING detected
    set aws_region=us-west-2
    set bucket_name=seer-internalms
    set env_access_key_var=SEER_AWS_ACCESS_KEY_ID_US
    set env_secret_key_var=SEER_AWS_SECRET_ACCESS_KEY_US
) else if not "%fileName:GER=%"=="%fileName%" (
    :: GER detected
    set aws_region=eu-central-1
    set bucket_name=seer-internalms-eu
    set env_access_key_var=SEER_AWS_ACCESS_KEY_ID_GER
    set env_secret_key_var=SEER_AWS_SECRET_ACCESS_KEY_GER
) else if not "%fileName:EUTESTING=%"=="%fileName%" (
    :: EUTESTING detected
    set aws_region=eu-central-1
    set bucket_name=seer-internalms-eu
    set env_access_key_var=SEER_AWS_ACCESS_KEY_ID_GER
    set env_secret_key_var=SEER_AWS_SECRET_ACCESS_KEY_GER
) else (
    echo The file name must contain 'EXP', 'USTESTING', 'GER', or 'EUTESTING' to determine AWS credentials.
    exit /B -1
)

call set "AWS_ACCESS_KEY_ID=%%%env_access_key_var%%%"
call set "AWS_SECRET_ACCESS_KEY=%%%env_secret_key_var%%%"
set "AWS_DEFAULT_REGION=%aws_region%"

if "%AWS_ACCESS_KEY_ID%" == "" (
    echo Missing required environment variable %env_access_key_var% >> %watchdog_batch_script_log%
    exit /B -1
)

if "%AWS_SECRET_ACCESS_KEY%" == "" (
    echo Missing required environment variable %env_secret_key_var% >> %watchdog_batch_script_log%
    exit /B -1
)

:: Execute seer_watchdog.py and log output
python C:\seer-scripts\watchdog3\seer_watchdog.py --aws-region "%aws_region%" --source "%sourceDir%" --bucket "%bucket_name%" --instrument Thermo --destination S3 --log_group ms_data_log_group --log_stream ms_data_log_stream >> %watchdog_batch_script_log% 2>&1

:: Check if the Python script executed successfully.
if %ERRORLEVEL% neq 0 (
    echo Error occurred during script execution >> %watchdog_batch_script_log%
    exit /B %ERRORLEVEL%
)

echo %DATE% %TIME% - Uploaded: %sourceDir% >> %watchdog_batch_script_log%
echo Script executed successfully >> %watchdog_batch_script_log%
exit /B 0
