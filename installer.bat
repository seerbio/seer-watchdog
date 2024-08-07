@echo off
set "USERNAME=%1"

:: Check if the USERNAME parameter is provided
if "%USERNAME%" == "" (
    echo You must provide the username as the first argument.
    echo Usage: install_data_transfer_utility.bat <username>
    exit /B -1
)

echo Installing Data Transfer Utility for user: %USERNAME%...

:: Step 1: Verify and Install Miniconda
if not exist "C:\Users\%USERNAME%\Miniconda3" (
    echo Miniconda not found. Downloading and installing Miniconda...
    curl -o Miniconda3-latest-Windows-x86_64.exe https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe
    start /wait "" Miniconda3-latest-Windows-x86_64.exe /InstallationType=JustMe /RegisterPython=0 /AddToPath=0 /S /D=C:\Users\%USERNAME%\Miniconda3
    del Miniconda3-latest-Windows-x86_64.exe
) else (
    echo Miniconda is already installed.
)

:: Step 2: Configure Environment Variables
setx PATH "C:\Users\%USERNAME%\Miniconda3;C:\Users\%USERNAME%\Miniconda3\Scripts;%PATH%"
setx PATH "C:\seer-scripts\watchdog3;%PATH%"
echo Environment variables configured.

:: Step 3: Restart Command Prompt to apply changes
echo Restarting Command Prompt to apply changes...
start cmd /k

:: Step 4: Install Python packages
call conda install -y python=3
call conda install -y pip
call pip install boto3 argparse awscli

:: Step 5: Configure AWS CLI
echo Configuring AWS CLI...
aws configure

:: Step 6: Clone or Download the Seer-Watchdog Repository
if not exist "C:\seer-scripts\watchdog3" (
    mkdir "C:\seer-scripts\watchdog3"
)
cd "C:\seer-scripts\watchdog3"
echo Copying seer_watchdog.py and seer_watchdog.bat to the directory...
:: Copy the scripts manually if not cloning from a repository
:: For cloning: git clone <repository_url> . (make sure git is installed)

:: Step 7: Verify Installation
echo Verifying installation...
python --version
conda --version
aws --version

echo Data Transfer Utility installation complete.
pause
