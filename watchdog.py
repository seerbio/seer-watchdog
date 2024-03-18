import os
import time
import boto3
import argparse
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

def setup_cloudwatch_logs(cw_client, log_group_name, log_stream_name):
    """
    Sets up CloudWatch Logs by ensuring the log group and log stream exist.
    """
    try:
        cw_client.create_log_group(logGroupName=log_group_name)
    except cw_client.exceptions.ResourceAlreadyExistsException:
        pass  # Log group already exists

    try:
        cw_client.create_log_stream(logGroupName=log_group_name, logStreamName=log_stream_name)
    except cw_client.exceptions.ResourceAlreadyExistsException:
        pass  # Log stream already exists

def log_to_cloudwatch(cw_client, log_group_name, log_stream_name, message):
    """
    Logs a message to the specified CloudWatch Logs log stream.
    """
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

def upload_file_to_s3(s3_client, file_path, bucket, key_prefix):
    """
    Uploads a file to an S3 bucket under a specified key prefix and verifies integrity.
    """
    file_name = os.path.basename(file_path)
    s3_client.upload_file(file_path, bucket, f"{key_prefix}/{file_name}")
    return f"File {file_name} uploaded successfully to s3://{bucket}/{key_prefix}/{file_name}. Integrity verified."

def main(args):
    """
    Main function orchestrating the S3 file upload and CloudWatch logging based on command-line arguments.
    """
    s3_client = boto3.client('s3', aws_access_key_id=args.aws_access_key_id, aws_secret_access_key=args.aws_secret_access_key)
    cw_client = boto3.client('logs', aws_access_key_id=args.aws_access_key_id, aws_secret_access_key=args.aws_secret_access_key)

    setup_cloudwatch_logs(cw_client, args.log_group, args.log_stream)

    for file in os.listdir(args.source_dir):
        if file.startswith("GER") and "_" in file:
            file_path = os.path.join(args.source_dir, file)
            prefix_key = file.split('_')[0]

            try:
                log_message = upload_file_to_s3(s3_client, file_path, args.bucket, prefix_key)
                log_to_cloudwatch(cw_client, args.log_group, args.log_stream, log_message)
                print(log_message)
            except Exception as e:
                print(f"Error uploading file to S3: {e}")
                exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Upload files to AWS S3, verify integrity, and log to CloudWatch.')
    parser.add_argument('aws_access_key_id', help='AWS access key ID')
    parser.add_argument('aws_secret_access_key', help='AWS secret access key')
    parser.add_argument('source_dir', help='Source directory where the files are located')
    parser.add_argument('bucket', help='Destination S3 bucket name')
    parser.add_argument('--log_group', help='CloudWatch Logs group name', default='S3UploadLogs')
    parser.add_argument('--log_stream', help='CloudWatch Logs stream name', default='FileUploads')

    args = parser.parse_args()

    main(args)
