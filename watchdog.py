import os
import time
import boto3
import argparse
import shutil
import hashlib
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

def setup_cloudwatch_logs(cw_client, log_group_name, log_stream_name):
    """Sets up CloudWatch Logs by ensuring the log group and log stream exist."""
    try:
        cw_client.create_log_group(logGroupName=log_group_name)
    except cw_client.exceptions.ResourceAlreadyExistsException:
        pass  # Log group already exists

    try:
        cw_client.create_log_stream(logGroupName=log_group_name, logStreamName=log_stream_name)
    except cw_client.exceptions.ResourceAlreadyExistsException:
        pass  # Log stream already exists

def log_to_cloudwatch(cw_client, log_group_name, log_stream_name, message):
    """Logs a message to the specified CloudWatch Logs log stream and locally."""
    response = cw_client.describe_log_streams(logGroupName=log_group_name, logStreamNamePrefix=log_stream_name)
    upload_sequence_token = response['logStreams'][0].get('uploadSequenceToken', '0')

    cw_client.put_log_events(
        logGroupName=log_group_name,
        logStreamName=log_stream_name,
        logEvents=[{
            'timestamp': int(round(time.time() * 1000)),
            'message': message
        }],
        sequenceToken=upload_sequence_token
    )
    log_locally(message)

def log_locally(message):
    """Logs a message to a local log file in the same directory as the program file."""
    with open("local_log.txt", "a") as log_file:
        log_file.write(f"{time.ctime()}: {message}\n")

def zip_directory(source_dir, zip_name):
    """Zips the specified directory and saves the archive with the given name."""
    shutil.make_archive(zip_name, 'zip', source_dir)
    return f"{zip_name}.zip"

def upload_file_to_s3(s3_client, file_path, bucket, key_prefix):
    """Uploads a file to an S3 bucket under a specified key prefix and verifies integrity."""
    file_name = os.path.basename(file_path)
    s3_client.upload_file(file_path, bucket, f"{key_prefix}/{file_name}")
    return f"File {file_name} uploaded successfully to s3://{bucket}/{key_prefix}/{file_name}. Integrity verified."

def copy_file_to_directory(source, destination, file_name):
    """Copies a file to the specified directory and verifies the file integrity via checksum."""
    destination_path = os.path.join(destination, file_name)
    shutil.copy2(source, destination_path)

    # Verify checksum
    original_checksum = calculate_checksum(source)
    copied_checksum = calculate_checksum(destination_path)

    if original_checksum == copied_checksum:
        return f"File {file_name} copied successfully to {destination}. Integrity verified."
    else:
        return "Error: File integrity could not be verified after copying."

def calculate_checksum(file_path):
    """Calculates the MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def main(args):
    """Orchestrates the conditional zipping, copying, and uploading of files or directories based on the instrument type and destination."""
    try:
        if args.destination == 'S3':
            s3_client = boto3.client('s3', aws_access_key_id=args.aws_access_key_id, aws_secret_access_key=args.aws_secret_access_key)
            cw_client = boto3.client('logs', aws_access_key_id=args.aws_access_key_id, aws_secret_access_key=args.aws_secret_access_key)
            setup_cloudwatch_logs(cw_client, args.log_group, args.log_stream)

        file_to_transfer = ''
        if args.instrument in ['Bruker', 'Sciex']:
            # Assuming directories with specific extensions for Bruker and Sciex
            extension = '.d' if args.instrument == 'Bruker' else '.wiff'
            directories = [d for d in os.listdir(args.source_dir) if os.path.isdir(os.path.join(args.source_dir, d)) and d.endswith(extension)]
            if not directories:
                print(f"No directories with the extension {extension} were found in {args.source_dir}.")
                exit(1)
            # Choose the first directory that matches the criteria
            source = os.path.join(args.source, directories[0])
            file_to_transfer = zip_directory(source, directories[0])
        elif args.instrument == 'Thermo':
            t = 0
            # file_path = args.source.strip()  # Ensure to strip any whitespace
            # if os.path.isfile(file_path):
            #     print(f"File exists: {file_path}")
            #     file_to_transfer = file_path
            # else:
            #     print(f"The specified source path for Thermo instrument is not a valid file: {args.source_dir}")
            #     exit(1)
        else:
            print("Unsupported instrument type.")
            exit(1)

        file_to_transfer = args.source
        file_name = os.path.basename(file_to_transfer)

        if args.destination == 'S3':
            key_prefix = "instrument_data"
            log_message = upload_file_to_s3(s3_client, file_to_transfer, args.bucket, key_prefix)
            log_to_cloudwatch(cw_client, args.log_group, args.log_stream, log_message)
        elif args.destination == 'Directory':
            if not os.path.exists(args.dest):
                os.makedirs(args.dest)
            log_message = copy_file_to_directory(file_to_transfer, args.dest, file_name)
            log_locally(log_message)
            print(log_message)
        else:
            print("Unsupported destination.")
            exit(1)

    except NoCredentialsError:
        message = "No AWS credentials found. Please configure your AWS credentials."
        log_locally(message)
        print(message)
        exit(1)
    except PartialCredentialsError:
        message = "Incomplete AWS credentials. Please check your AWS access key ID and secret access key."
        log_locally(message)
        print(message)
        exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Conditionally zip a directory, upload it to AWS S3 or copy it to a local directory based on the instrument type and destination, verify integrity, and log both locally and to CloudWatch.')
    parser.add_argument('--aws_access_key_id', help='AWS access key ID (required only if destination is S3)', nargs='?', default=None)
    parser.add_argument('--aws_secret_access_key', help='AWS secret access key (required only if destination is S3)', nargs='?', default=None)
    parser.add_argument('--bucket', help='Destination S3 bucket name (required only if destination is S3)', default=None)
    parser.add_argument('--source', help='Source directory or file to be uploaded/copied', required=True)
    parser.add_argument('--dest', help='Destination directory for file copy (required only if destination is Directory)', default=None)
    parser.add_argument('--instrument', choices=['Bruker', 'Thermo', 'Sciex'], help='Type of instrument')
    parser.add_argument('--destination', choices=['S3', 'Directory'], help='Destination type: Upload to S3 or copy to a local directory')
    parser.add_argument('--log_group', help='CloudWatch Logs group name (required only if destination is S3)', default='S3UploadLogs')
    parser.add_argument('--log_stream', help='CloudWatch Logs stream name (required only if destination is S3)', default='InstrumentUploads')

    args = parser.parse_args()

    # Validate AWS credentials for S3 destination
    if args.destination == 'S3' and (not args.aws_access_key_id or not args.aws_secret_access_key or not args.bucket):
        print("AWS credentials and bucket name are required for S3 destination.")
        exit(1)
    
    # Validate destination directory for Directory destination
    if args.destination == 'Directory' and not args.dest:
        print("Destination directory is required for Directory destination.")
        exit(1)

    main(args)

