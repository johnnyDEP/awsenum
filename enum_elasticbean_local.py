#!/usr/bin/env python3
import boto3
import base64
import argparse
from rich.console import Console
from rich.table import Table
from botocore.exceptions import ClientError
import json

def decode_if_base64(value):
    try:
        return base64.b64decode(value).decode('utf-8')
    except:
        return value

def simulate_elasticbeanstalk_permissions(eb_client):
    actions = [
        'DescribeApplications',
        'DescribeEnvironments',
        'DescribeEvents',
        'DescribeInstancesHealth',
        'DescribePlatformVersion',
        'ListAvailableSolutionStacks',
        'ListPlatformBranches',
        'ListPlatformVersions',
        'ListTagsForResource'
    ]
    
    results = []
    # Create an IAM client
    iam_client = boto3.client('iam')
    
    for action in actions:
        try:
            iam_client.simulate_principal_policy(
                PolicySourceArn='arn:aws:iam::aws:policy/AWSElasticBeanstalkFullAccess',
                ActionNames=[f'elasticbeanstalk:{action}']
            )
            results.append(f"✓ {action}")
        except ClientError as e:
            results.append(f"✗ {action}: {str(e)}")
    
    return results

def get_eb_applications(eb_client):
    try:
        response = eb_client.describe_applications()
        return response['Applications']
    except ClientError as e:
        print(f"Error fetching applications: {e}")
        return []

def create_rich_table(applications):
    table = Table(title="Elastic Beanstalk Applications")
    table.add_column("Application Name", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Date Created", style="yellow")
    table.add_column("Date Updated", style="yellow")
    table.add_column("Environments", style="magenta")
    table.add_column("Platform", style="blue")
    
    for app in applications:
        table.add_row(
            app.get('ApplicationName', 'N/A'),
            app.get('Description', 'N/A'),
            app.get('DateCreated', 'N/A'),
            app.get('DateUpdated', 'N/A'),
            str(len(app.get('Environments', []))),
            app.get('PlatformArn', 'N/A')
        )
    
    return table

def main():
    parser = argparse.ArgumentParser(description='AWS Elastic Beanstalk Application Information')
    parser.add_argument('--access-key', required=True, help='AWS Access Key (plaintext or base64 encoded)')
    parser.add_argument('--secret-key', required=True, help='AWS Secret Key (plaintext or base64 encoded)')
    parser.add_argument('--region', default='us-east-1', help='AWS Region (default: us-east-1)')
    
    args = parser.parse_args()
    
    # Decode credentials if they're base64 encoded
    access_key = decode_if_base64(args.access_key)
    secret_key = decode_if_base64(args.secret_key)
    
    # Create AWS session
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=args.region
    )
    
    # Create Elastic Beanstalk client
    eb_client = session.client('elasticbeanstalk')
    
    # Simulate permissions
    console = Console()
    console.print("\n[bold]Simulating Elastic Beanstalk Permissions:[/bold]")
    permissions = simulate_elasticbeanstalk_permissions(eb_client)
    for permission in permissions:
        console.print(permission)
    
    # Get applications
    console.print("\n[bold]Fetching Elastic Beanstalk Applications:[/bold]")
    applications = get_eb_applications(eb_client)
    
    if applications:
        table = create_rich_table(applications)
        console.print(table)
    else:
        console.print("[red]No applications found or error occurred[/red]")

if __name__ == "__main__":
    main()


