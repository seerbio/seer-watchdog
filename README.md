# Data Transfer Utility

## Overview

This utility script is designed to conditionally zip directories and transfer data either to AWS S3 or to a local directory, depending on the specified instrument type and destination. It supports instruments of types Bruker, Thermo, and Sciex. For Bruker and Sciex, the utility zips the specified directories (expecting `.d` and `.wiff` files respectively) before transfer. For Thermo, the `.raw` files are transferred without zipping. The script also verifies file integrity, logs actions locally, and to AWS CloudWatch.

## Requirements

- Python 3.x
- Boto3 Argparse
- AWS CLI (configured with access key and secret access key)
- Access to an AWS S3 bucket (for S3 uploads)

## Setup

1. Ensure Python 3.x is installed on your system.
2. Install Boto3 and ArgParse by running `pip install boto3 argparse`.
3. Configure AWS CLI with your AWS credentials (`aws_access_key_id` and `aws_secret_access_key`) by running `aws configure`.

## Usage

### Basic Command Structure

```shell
python seer_watchdog.py --source <SOURCE> --dest <DESTINATION_PATH> --instrument <INSTRUMENT_TYPE> --destination <DESTINATION_TYPE> [--bucket <BUCKET_NAME>] [--aws_access_key_id <ACCESS_KEY>] [--aws_secret_access_key <SECRET_KEY>] [--log_group <LOG_GROUP>] [--log_stream <LOG_STREAM>]

usage: seer_watchdog.py [-h] [--aws_access_key_id AWS_ACCESS_KEY_ID]
                        [--aws_secret_access_key AWS_SECRET_ACCESS_KEY]
                        --source SOURCE [--bucket BUCKET] [--dest DEST]
                        --instrument {Bruker,Thermo,Sciex} --destination
                        {S3,Directory} [--log_group LOG_GROUP]
                        [--log_stream LOG_STREAM]

Zip Bruker and Sciex *.wiff and *.d directories (or transfer Thermo *.raw),
upload it to AWS S3 or copy it to a local directory based on the instrument
type and destination, verify integrity, and log both locally and to
CloudWatch.

optional arguments:
  -h, --help            show this help message and exit
  --aws_access_key_id AWS_ACCESS_KEY_ID
                        AWS access key ID (required only if destination is S3)
  --aws_secret_access_key AWS_SECRET_ACCESS_KEY
                        AWS secret access key (required only if destination is S3)
  --source SOURCE       Source directory or file to be uploaded/copied
  --bucket BUCKET       Destination S3 bucket name (required only if destination is S3)
  --dest DEST           Destination directory for file copy (required only if destination is Directory)
  --instrument {Bruker,Thermo,Sciex} Type of instrument
  --destination {S3,Directory} Destination type: Upload to S3 or copy to a local directory
  --log_group LOG_GROUP CloudWatch Logs group name (required only if destination is S3)
  --log_stream LOG_STREAM CloudWatch Logs stream name (required only if destination is S3)
