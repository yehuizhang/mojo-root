#!/usr/bin/env python3
"""
Compare a local file with a file in AWS S3
Usage: python s3_file_diff.py local_file.txt s3://bucket/path/file.txt
"""

import sys
import boto3
import difflib
from pathlib import Path

def compare_files(local_file_path, s3_uri):
    # Parse S3 URI
    if not s3_uri.startswith('s3://'):
        raise ValueError("S3 URI must start with 's3://'")
    
    s3_path = s3_uri[5:]  # Remove 's3://'
    bucket, key = s3_path.split('/', 1)
    
    # Read local file
    try:
        with open(local_file_path, 'r', encoding='utf-8') as f:
            local_content = f.readlines()
    except Exception as e:
        print(f"Error reading local file: {e}")
        return False
    
    # Read S3 file
    try:
        s3 = boto3.client('s3')
        response = s3.get_object(Bucket=bucket, Key=key)
        s3_content = response['Body'].read().decode('utf-8').splitlines(keepends=True)
    except Exception as e:
        print(f"Error reading S3 file: {e}")
        return False
    
    # Compare files
    diff = list(difflib.unified_diff(
        local_content, 
        s3_content,
        fromfile=f'local: {local_file_path}',
        tofile=f's3: {s3_uri}',
        lineterm=''
    ))
    
    if diff:
        print("Files are different:")
        print('\n'.join(diff))
        return False
    else:
        print("Files are identical")
        return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python s3_file_diff.py <local_file> <s3_uri>")
        print("Example: python s3_file_diff.py config.yml s3://my-bucket/config.yml")
        sys.exit(1)
    
    local_file = sys.argv[1]
    s3_uri = sys.argv[2]
    
    compare_files(local_file, s3_uri)