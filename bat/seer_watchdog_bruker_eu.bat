@echo off
set param1=%1
set sourceDir=%2

:: Check if the source directory argument is provided
if "%~2" == "" (
    echo You must provide the source directory as the second argument.
    exit /B -1
)

set watchdog_batch_script_log=C:/seer-watchdog/watchdog3/script_logs
echo %DATE% %TIME% - param1 is %param1% >> %watchdog_batch_script_log%
echo %DATE% %TIME% - Invoked with directory: %sourceDir% >> %watchdog_batch_script_log%

:: Log the execution of seer_watchdog.py
echo %DATE% %TIME% - Executing seer_watchdog.py with directory: %sourceDir% >> %watchdog_batch_script_log%

:: Execute seer_watchdog.py and log output
python E:\git\seer-watchdog\seer_watchdog.py --aws_access_key_id "" --aws_secret_access_key "" --aws-region us-west-2 --source "%sourceDir%" --bucket seer-de-test-bucket --instrument Bruker --destination S3 --log_group ms_data_log_group --log_stream ms_data_log_stream >> %watchdog_batch_script_log% 2>&1

:: Check if the Python script executed successfully.
if %ERRORLEVEL% neq 0 (
    echo Error occurred during script execution >> %watchdog_batch_script_log%
    exit /B %ERRORLEVEL%
)

echo %DATE% %TIME% - Zipped and uploaded: %sourceDir% >> %watchdog_batch_script_log%

echo Script executed successfully >> %watchdog_batch_script_log%
exit /B 0
