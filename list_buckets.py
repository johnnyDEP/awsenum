import boto3
import base64
from botocore.exceptions import ClientError
from rich.console import Console
from rich.table import Table
import argparse

def decode_base64_key(encoded_key):
    """Decode base64 encoded key if necessary"""
    try:
        return base64.b64decode(encoded_key).decode('utf-8')
    except:
        return encoded_key  # Return as-is if not base64 encoded

def get_user_id(access_key, secret_key):
    """Get AWS user ID using the provided credentials"""
    try:
        sts_client = boto3.client(
            'sts',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        identity = sts_client.get_caller_identity()
        return identity['UserId'], identity['Arn']
    except ClientError as e:
        return None, f"Error: {str(e)}"

def list_accessible_buckets(access_key, secret_key):
    """List all S3 buckets and test basic accessibility"""
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        
        # Get list of all buckets
        response = s3_client.list_buckets()
        buckets = response['Buckets']
        
        bucket_info = []
        
        for bucket in buckets:
            bucket_name = bucket['Name']
            bucket_details = {
                'Name': bucket_name,
                'CreationDate': bucket['CreationDate'].strftime('%Y-%m-%d %H:%M:%S'),
                'CanList': False,
                'CanGet': False,
                'CanPut': False,
                'Location': 'Unknown'
            }
            
            # Test basic permissions
            try:
                # Test listing objects
                s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
                bucket_details['CanList'] = True
            except ClientError:
                pass
                
            try:
                # Test getting bucket location
                location = s3_client.get_bucket_location(Bucket=bucket_name)
                bucket_details['Location'] = location['LocationConstraint'] or 'us-east-1'
            except ClientError:
                pass
                
            try:
                # Test putting an object (using a test key)
                test_key = 'test-access-check.txt'
                s3_client.put_object(Bucket=bucket_name, Key=test_key, Body='test')
                bucket_details['CanPut'] = True
                # Clean up test object
                s3_client.delete_object(Bucket=bucket_name, Key=test_key)
            except ClientError:
                pass
                
            try:
                # Test getting an object (assuming we can put first)
                if bucket_details['CanPut']:
                    test_key = 'test-access-check.txt'
                    s3_client.put_object(Bucket=bucket_name, Key=test_key, Body='test')
                    s3_client.get_object(Bucket=bucket_name, Key=test_key)
                    bucket_details['CanGet'] = True
                    s3_client.delete_object(Bucket=bucket_name, Key=test_key)
            except ClientError:
                pass
                
            bucket_info.append(bucket_details)
        
        return bucket_info
    
    except ClientError as e:
        return None, f"Error accessing S3: {str(e)}"

def display_bucket_info(user_id, arn, bucket_info):
    """Display bucket information in a rich table"""
    console = Console()
    
    # Display user info
    console.print(f"[bold green]User ID:[/bold green] {user_id}")
    console.print(f"[bold green]ARN:[/bold green] {arn}")
    console.print()
    
    # Create table
    table = Table(title="Accessible S3 Buckets")
    table.add_column("Bucket Name", style="cyan", no_wrap=True)
    table.add_column("Creation Date", style="magenta")
    table.add_column("Location", style="green")
    table.add_column("Can List", justify="center")
    table.add_column("Can Get", justify="center")
    table.add_column("Can Put", justify="center")
    
    for bucket in bucket_info:
        table.add_row(
            bucket['Name'],
            bucket['CreationDate'],
            bucket['Location'],
            "[green]✓[/green]" if bucket['CanList'] else "[red]✗[/red]",
            "[green]✓[/green]" if bucket['CanGet'] else "[red]✗[/red]",
            "[green]✓[/green]" if bucket['CanPut'] else "[red]✗[/red]"
        )
    
    console.print(table)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='AWS S3 Bucket Enumeration Tool')
    parser.add_argument('--access-key', required=True, help='AWS Access Key (plain or base64 encoded)')
    parser.add_argument('--secret-key', required=True, help='AWS Secret Key (plain or base64 encoded)')
    args = parser.parse_args()
    
    # Decode keys if necessary
    access_key = decode_base64_key(args.access_key)
    secret_key = decode_base64_key(args.secret_key)
    
    # Get user ID and ARN
    user_id, arn = get_user_id(access_key, secret_key)
    
    if user_id:
        # Get bucket information
        bucket_info = list_accessible_buckets(access_key, secret_key)
        
        if isinstance(bucket_info, list):
            display_bucket_info(user_id, arn, bucket_info)
        else:
            console = Console()
            console.print(f"[bold red]Failed to enumerate buckets: {bucket_info[1]}[/bold red]")
    else:
        console = Console()
        console.print(f"[bold red]Failed to authenticate: {arn}[/bold red]")

if __name__ == "__main__":
    main()
