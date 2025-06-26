#!/usr/bin/env python3

import boto3
import argparse
from rich.console import Console
from rich.table import Table
from botocore.exceptions import ClientError, NoCredentialsError

def get_all_regions(ec2_client):
    """Get list of all available AWS regions"""
    response = ec2_client.describe_regions()
    return [region['RegionName'] for region in response['Regions']]

def get_ec2_instances(access_key, secret_key):
    """Fetch EC2 instances from all regions"""
    # Initialize console for rich output
    console = Console()
    
    # Set up AWS session with provided credentials
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )
    
    # Get all regions
    ec2_client = session.client('ec2')
    regions = get_all_regions(ec2_client)
    
    # Store all instance details
    all_instances = []
    
    # Iterate through each region
    for region in regions:
        try:
            # Create region-specific EC2 client
            ec2 = session.client('ec2', region_name=region)
            
            # Get instance details
            response = ec2.describe_instances()
            
            # Process each reservation and instance
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_details = {
                        'Region': region,
                        'InstanceId': instance.get('InstanceId', 'N/A'),
                        'InstanceType': instance.get('InstanceType', 'N/A'),
                        'State': instance.get('State', {}).get('Name', 'N/A'),
                        'PublicIP': instance.get('PublicIpAddress', 'N/A'),
                        'PrivateIP': instance.get('PrivateIpAddress', 'N/A'),
                        'LaunchTime': str(instance.get('LaunchTime', 'N/A')),
                        'Name': 'N/A'  # Default value for Name tag
                    }
                    
                    # Extract Name tag if it exists
                    if 'Tags' in instance:
                        for tag in instance['Tags']:
                            if tag['Key'] == 'Name':
                                instance_details['Name'] = tag['Value']
                                break
                    
                    all_instances.append(instance_details)
                    
        except ClientError as e:
            console.print(f"[red]Error accessing region {region}: {str(e)}[/red]")
        except Exception as e:
            console.print(f"[red]Unexpected error in region {region}: {str(e)}[/red]")
    
    return all_instances

def display_instances(instances):
    """Display instances in a rich table"""
    console = Console()
    
    # Create table
    table = Table(title="AWS EC2 Instances Across All Regions")
    
    # Add columns
    table.add_column("Region", style="cyan")
    table.add_column("Instance ID", style="magenta")
    table.add_column("Name", style="green")
    table.add_column("Type", style="blue")
    table.add_column("State", style="yellow")
    table.add_column("Public IP", style="white")
    table.add_column("Private IP", style="white")
    table.add_column("Launch Time", style="white")
    
    # Add rows
    for instance in instances:
        table.add_row(
            instance['Region'],
            instance['InstanceId'],
            instance['Name'],
            instance['InstanceType'],
            instance['State'],
            instance['PublicIP'],
            instance['PrivateIP'],
            instance['LaunchTime']
        )
    
    # Display table
    console.print(table)
    console.print(f"\nTotal instances found: {len(instances)}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='List AWS EC2 instances across all regions')
    parser.add_argument('--access-key', required=True, help='AWS Access Key ID')
    parser.add_argument('--secret-key', required=True, help='AWS Secret Access Key')
    
    args = parser.parse_args()
    
    console = Console()
    
    try:
        console.print("[green]Fetching EC2 instances... This may take a moment.[/green]")
        instances = get_ec2_instances(args.access_key, args.secret_key)
        display_instances(instances)
        
    except NoCredentialsError:
        console.print("[red]Error: Invalid AWS credentials provided[/red]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

if __name__ == "__main__":
    main()
