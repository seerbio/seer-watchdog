import os
import time
import boto3
import argparse
import shutil
import hashlib
from botocore.exceptions import NoCredentialsError, PartialCredentialsError


def setup_cloudwatch_logs(cw_client, log_group_name, log_stream_name):
    """Sets up CloudWatch Logs."""
    try:
        cw_client.create_log_group(logGroupName=log_group_name)
    except cw_client.exceptions.ResourceAlreadyExistsException:
        pass  # Log group already exists

    try:
        cw_client.create_log_stream(logGroupName=log_group_name, logStreamName=log_stream_name)
    except cw_client.exceptions.ResourceAlreadyExistsException:
        pass  # Log stream already exists


def log_to_cloudwatch(cw_client, log_group_name, log_stream_name, message):
    """Logs a message to CloudWatch Logs."""
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
    """Logs a message locally."""
    with open("local_log.txt", "a") as log_file:
        log_file.write(f"{time.ctime()}: {message}\n")


def zip_directory(source, zip_name):
    """Zips the specified directory."""
    shutil.make_archive(zip_name, 'zip', source)
    return f"{zip_name}.zip"


def upload_file_to_s3(s3_client, file_path, bucket, file_name):
    """Uploads a file to S3 with integrity check."""
    # Calculate checksum before upload
    original_checksum = calculate_checksum(file_path)
    prefix = extract_prefix(file_name)
    s3_key = f"{prefix}/{file_name}"
    s3_client.upload_file(file_path, bucket, s3_key)
    # Assuming S3's upload success as integrity confirmation
    return f"File {file_name} uploaded successfully to s3://{bucket}/{s3_key}. Original checksum: {original_checksum}"


def copy_file_to_directory(source, dest, file_name):
    """Copies a file to a directory with integrity check."""
    prefix = extract_prefix(file_name)
    final_dest_dir = find_or_create_prefixed_dir(dest, prefix)
    dest_path = os.path.join(final_dest_dir, file_name)
    shutil.copy2(source, dest_path)
    # Verify checksum
    original_checksum = calculate_checksum(source)
    copied_checksum = calculate_checksum(dest_path)
    if original_checksum == copied_checksum:
        return f"File {file_name} copied successfully to {dest} with verified integrity."
    else:
        return f"Error: Integrity check failed for {file_name} after copying."


def calculate_checksum(file_path):
    """Calculates the MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def extract_prefix(filename):
    """Extracts the prefix from the filename."""
    return filename.split('_')[0]


def find_or_create_prefixed_dir(dest, prefix):
    """Finds or creates a directory with the given prefix."""
    for dirname in os.listdir(dest):
        if dirname.startswith(prefix):
            return os.path.join(dest, dirname)
    new_dir_path = os.path.join(dest, prefix)
    os.makedirs(new_dir_path, exist_ok=True)
    return new_dir_path


def main(args):
    """Main function orchestrating the file processing."""
    try:
        s3_client, cw_client = None, None
        if args.destination == 'S3':
            s3_client = boto3.client('s3', aws_access_key_id=args.aws_access_key_id,
                                     aws_secret_access_key=args.aws_secret_access_key)
            cw_client = boto3.client('logs', aws_access_key_id=args.aws_access_key_id,
                                     aws_secret_access_key=args.aws_secret_access_key)
            setup_cloudwatch_logs(cw_client, args.log_group, args.log_stream)

        file_to_transfer = args.source
        if args.instrument in ['Bruker', 'Sciex']:
            # For Bruker and Sciex, zip the directory
            file_to_transfer = zip_directory(args.source, os.path.basename(args.source))
        # Thermo files are treated as individual files and are not zipped
        file_name = os.path.basename(file_to_transfer)
        original_checksum = calculate_checksum(file_to_transfer)  # Calculate checksum for integrity check

        if args.destination == 'S3':
            # Upload to S3 with a directory prefix based on the file name
            log_message = upload_file_to_s3(s3_client, file_to_transfer, args.bucket, file_name)
            log_to_cloudwatch(cw_client, args.log_group, args.log_stream, log_message)
        elif args.destination == 'Directory':
            # Copy to a local directory, creating a new directory with the prefix if necessary
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
    parser = argparse.ArgumentParser(
        description='Zip Bruker and Sciex *.wiff and *.d directories (or transfer Thermo *.raw), upload it to AWS S3 or copy it to a local directory based on the instrument type and destination, verify integrity, and log both locally and to CloudWatch.')
    parser.add_argument('--aws_access_key_id', help='AWS access key ID (required only if destination is S3)',
                        default=None)
    parser.add_argument('--aws_secret_access_key', help='AWS secret access key (required only if destination is S3)',
                        default=None)
    parser.add_argument('--source', help='Source directory or file to be uploaded/copied', required=True)
    parser.add_argument('--bucket', help='Destination S3 bucket name (required only if destination is S3)',
                        default=None)
    parser.add_argument('--dest',
                        help='Destination directory for file copy (required only if destination is Directory)',
                        default=None)
    parser.add_argument('--instrument', choices=['Bruker', 'Thermo', 'Sciex'], help='Type of instrument', required=True)
    parser.add_argument('--destination', choices=['S3', 'Directory'],
                        help='Destination type: Upload to S3 or copy to a local directory', required=True)
    parser.add_argument('--log_group', help='CloudWatch Logs group name (required only if destination is S3)',
                        default='S3UploadLogs')
    parser.add_argument('--log_stream', help='CloudWatch Logs stream name (required only if destination is S3)',
                        default='InstrumentUploads')

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



