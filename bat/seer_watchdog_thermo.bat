@echo off
set sourceDir=%1

:: Check if the source directory argument is provided
if "%~1" == "" (
    echo You must provide the *.raw file path.
    exit /B -1
)

set watchdog_batch_script_log=C:\seer-scripts\watchdog3\script_logs
echo %DATE% %TIME% - Invoked with Thermo Raw File: %sourceDir% >> %watchdog_batch_script_log%

:: Log the execution of seer_watchdog.py
echo %DATE% %TIME% - Executing seer_watchdog.py with directory: %sourceDir% >> %watchdog_batch_script_log%

:: Determine which AWS credentials and bucket to use based on source directory argument
if "%sourceDir:EXP=%" neq "%sourceDir%" if "%sourceDir:USTESTING=%" neq "%sourceDir%" (
    :: EXP or USTESTING detected
    set "aws_access_key_id=YOUR_AWS_ACCESS_KEY_ID_US"
    set "aws_secret_access_key=YOUR_AWS_SECRET_ACCESS_KEY_US"
    set "aws_region=us-west-2"
    set "bucket_name=seer-internalms"
) else if "%sourceDir:GER=%" neq "%sourceDir%" if "%sourceDir:EUTESTING=%" neq "%sourceDir%" (
    :: GER or EUTESTING detected
    set "aws_access_key_id=YOUR_AWS_ACCESS_KEY_ID_GER"
    set "aws_secret_access_key=YOUR_AWS_SECRET_ACCESS_KEY_GER"
    set "aws_region=eu-central-1"
    set "bucket_name=seer-internalms-eu"
) else (
    echo Source directory must contain 'EXP', 'USTESTING', 'GER', or 'EUTESTING' to determine AWS credentials.
    exit /B -1
)

:: Execute seer_watchdog.py and log output
python C:\seer-scripts\watchdog3\seer_watchdog.py --aws_access_key_id "%aws_access_key_id%" --aws_secret_access_key "%aws_secret_access_key%" --aws-region "%aws_region%" --source "%sourceDir%" --bucket "%bucket_name%" --instrument Thermo --destination S3 --log_group ms_data_log_group --log_stream ms_data_log_stream >> %watchdog_batch_script_log% 2>&1

:: Check if the Python script executed successfully.
if %ERRORLEVEL% neq 0 (
    echo Error occurred during script execution >> %watchdog_batch_script_log%
    exit /B %ERRORLEVEL%
)

echo %DATE% %TIME% - Uploaded: %sourceDir% >> %watchdog_batch_script_log%

echo Script executed successfully >> %watchdog_batch_script_log%
exit /B 0
