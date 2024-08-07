@echo off
set param1=%1
set sourceDir=%2

:: Check if the source directory argument is provided
if "%~2" == "" (
    echo You must provide the source directory as the second argument.
    exit /B -1
)
set watchdog_batch_script_log=C:\seer-scripts\watchdog3\script_logs
echo %DATE% %TIME% - Invoked with Bruker .d File: %sourceDir% >> %watchdog_batch_script_log%

:: Log the execution of seer_watchdog.py
echo %DATE% %TIME% - Executing seer_watchdog.py with directory: %sourceDir% >> %watchdog_batch_script_log%

:: Determine which AWS credentials and bucket to use based on source directory argument
echo %sourceDir% | findstr /i /c:"EXP" /c:"USTESTING" >nul
if %ERRORLEVEL% equ 0 (
    :: EXP or USTESTING detected
    set "aws_access_key_id=AKIA2OXTCKO6F6EKYPUN"
    set "aws_secret_access_key=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"
    set "aws_region=us-west-2"
    set "bucket_name=seer-internalms"
) else (
    echo %sourceDir% | findstr /i /c:"GER" /c:"EUTESTING" >nul
    if %ERRORLEVEL% equ 0 (
        :: GER or EUTESTING detected
        set "aws_access_key_id=YOUR_AWS_ACCESS_KEY_ID_GER"
        set "aws_secret_access_key=YOUR_AWS_SECRET_ACCESS_KEY_GER"
        set "aws_region=eu-central-1"
        set "bucket_name=seer-internalms-eu"
    ) else (
        echo Source directory must contain 'EXP', 'USTESTING', 'GER', or 'EUTESTING' to determine AWS credentials.
        exit /B -1
    )
)

:: Execute seer_watchdog.py and log output
python C:\seer-scripts\watchdog3\seer_watchdog.py --aws_access_key_id "%aws_access_key_id%" --aws_secret_access_key "%aws_secret_access_key%" --aws-region "%aws_region%" --source "%sourceDir%" --bucket "%bucket_name%" --instrument Bruker --destination S3 --log_group ms_data_log_group --log_stream ms_data_log_stream >> %watchdog_batch_script_log% 2>&1

:: Check if the Python script executed successfully.
if %ERRORLEVEL% neq 0 (
    echo Error occurred during script execution >> %watchdog_batch_script_log%
    exit /B %ERRORLEVEL%
)

echo %DATE% %TIME% - Uploaded: %sourceDir% >> %watchdog_batch_script_log%

echo Script executed successfully >> %watchdog_batch_script_log%
exit /B 0
