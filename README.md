# Data Transfer Utility

## Overview

This utility script is designed to conditionally zip directories and transfer data either to AWS S3 or to a local directory, depending on the specified instrument type and destination. It supports instruments of types Bruker, Thermo, and Sciex. For Bruker and Sciex, the utility zips the specified directories (expecting `.d` and `.wiff` files respectively) before transfer. For Thermo, the `.raw` files are transferred without zipping. The script also verifies file integrity, logs actions locally, and to AWS CloudWatch.

## Requirements

- Python 3.x
- Boto3
- AWS CLI (configured with access key and secret access key)
- Access to an AWS S3 bucket (for S3 uploads)

## Setup

1. Ensure Python 3.x is installed on your system.
2. Install Boto3 by running `pip install boto3`.
3. Configure AWS CLI with your AWS credentials (`aws_access_key_id` and `aws_secret_access_key`) by running `aws configure`.

## Usage

### Basic Command Structure

```shell
python seer_watchdog.py --source <SOURCE> --dest <DESTINATION_PATH> --instrument <INSTRUMENT_TYPE> --destination <DESTINATION_TYPE> [--bucket <BUCKET_NAME>] [--aws_access_key_id <ACCESS_KEY>] [--aws_secret_access_key <SECRET_KEY>] [--log_group <LOG_GROUP>] [--log_stream <LOG_STREAM>]
