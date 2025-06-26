#!/usr/bin/env python3
import boto3
import base64
import argparse
from rich.console import Console
from rich.table import Table
from botocore.exceptions import ClientError

def decode_if_base64(value):
    try:
        return base64.b64decode(value).decode('utf-8')
    except:
        return value

def list_s3_buckets(s3_client):
    try:
        response = s3_client.list_buckets()
        return response['Buckets']
    except ClientError as e:
        print(f"Error listing buckets: {e}")
        return []

def list_bucket_contents(s3_client, bucket_name):
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        return response.get('Contents', [])
    except ClientError as e:
        print(f"Error listing contents of bucket {bucket_name}: {e}")
        return []

def create_rich_table(contents):
    table = Table(title="S3 Bucket Contents")
    table.add_column("Key", style="cyan")
    table.add_column("Size (bytes)", style="green")
    table.add_column("Last Modified", style="yellow")
    table.add_column("Storage Class", style="magenta")
    
    for item in contents:
        table.add_row(
            item.get('Key', 'N/A'),
            str(item.get('Size', 'N/A')),
            str(item.get('LastModified', 'N/A')),
            item.get('StorageClass', 'N/A')
        )
    
    return table

def main():
    parser = argparse.ArgumentParser(description='AWS S3 Bucket Contents Lister')
    parser.add_argument('--access-key', required=True, help='AWS Access Key (plaintext or base64 encoded)')
    parser.add_argument('--secret-key', required=True, help='AWS Secret Key (plaintext or base64 encoded)')
    parser.add_argument('--bucket', required=True, help='S3 Bucket name to list contents')
    
    args = parser.parse_args()
    
    # Decode credentials if they're base64 encoded
    access_key = decode_if_base64(args.access_key)
    secret_key = decode_if_base64(args.secret_key)
    
    # Static list of AWS regions
    regions = [
        'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
        'eu-west-1', 'eu-west-2', 'eu-central-1',
        'ap-southeast-1', 'ap-southeast-2',
        'ap-northeast-1', 'ap-northeast-2',
        'sa-east-1'
    ]
    
    console = Console()
    
    for region in regions:
        console.print(f"\n[bold]Checking region: {region}[/bold]")
        
        # Create AWS session for each region
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        # Create S3 client
        s3_client = session.client('s3')
        
        try:
            # Try to list contents of the specified bucket
            contents = list_bucket_contents(s3_client, args.bucket)
            
            if contents:
                console.print(f"[green]Found contents in bucket {args.bucket} in region {region}[/green]")
                table = create_rich_table(contents)
                console.print(table)
                break  # Exit loop if we found the bucket
            else:
                console.print(f"[yellow]No contents found in bucket {args.bucket} in region {region}[/yellow]")
                
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                console.print(f"[yellow]Bucket {args.bucket} not found in region {region}[/yellow]")
            else:
                console.print(f"[red]Error accessing bucket in region {region}: {e}[/red]")

if __name__ == "__main__":
    main()
