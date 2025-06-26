import boto3
import base64
from botocore.exceptions import ClientError
from rich.console import Console
from rich.table import Table
from datetime import datetime
import argparse

def decode_base64_key(encoded_key):
    """Decode base64 encoded key if necessary"""
    try:
        return base64.b64decode(encoded_key).decode('utf-8')
    except:
        return encoded_key  # Return as-is if not base64 encoded

# Static list of AWS regions (as of April 2025 - update as needed)
AWS_REGIONS = [
    'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
    'af-south-1', 'ap-east-1', 'ap-south-1',
    'ap-northeast-1', 'ap-northeast-2', 'ap-northeast-3',
    'ap-southeast-1', 'ap-southeast-2', 'ap-southeast-3',
    'ca-central-1', 'ca-west-1',
    'eu-central-1', 'eu-central-2', 'eu-west-1', 'eu-west-2',
    'eu-west-3', 'eu-south-1', 'eu-south-2', 'eu-north-1',
    'me-south-1', 'me-central-1', 'sa-east-1',
    # Add more regions as AWS expands
]

def get_elasticbeanstalk_details(access_key, secret_key, regions):
    """Get detailed information about Elastic Beanstalk applications in specified regions"""
    console = Console()
    all_applications = {}
    
    for region in regions:
        try:
            # Create Elastic Beanstalk client for the region
            eb_client = boto3.client(
                'elasticbeanstalk',
                region_name=region,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            )
            
            # Test connection by making a simple API call
            eb_client.describe_applications()
            
        except ClientError as e:
            console.print(f"[yellow]Warning: Could not connect to Elastic Beanstalk in {region}: {str(e)}. Skipping this region.[/yellow]")
            continue
            
        try:
            # Get all applications in the region
            apps_response = eb_client.describe_applications()
            applications = apps_response.get('Applications', [])
            
            if not applications:
                console.print(f"[yellow]No applications found in {region}[/yellow]")
                continue
                
            # Store applications with region
            all_applications[region] = []
            
            for app in applications:
                app_details = {
                    'ApplicationName': app.get('ApplicationName', 'N/A'),
                    'Description': app.get('Description', 'N/A'),
                    'DateCreated': app.get('DateCreated', 'N/A'),
                    'DateUpdated': app.get('DateUpdated', 'N/A'),
                    'Environments': [],
                    'ConfigurationTemplates': app.get('ConfigurationTemplates', []),
                    'ResourceLifecycleConfig': app.get('ResourceLifecycleConfig', {})
                }
                
                # Get environment details for this application
                try:
                    env_response = eb_client.describe_environments(
                        ApplicationName=app['ApplicationName']
                    )
                    for env in env_response.get('Environments', []):
                        env_details = {
                            'EnvironmentName': env.get('EnvironmentName', 'N/A'),
                            'Status': env.get('Status', 'N/A'),
                            'Health': env.get('Health', 'N/A'),
                            'HealthStatus': env.get('HealthStatus', 'N/A'),
                            'VersionLabel': env.get('VersionLabel', 'N/A'),
                            'SolutionStackName': env.get('SolutionStackName', 'N/A'),
                            'DateCreated': env.get('DateCreated', 'N/A'),
                            'DateUpdated': env.get('DateUpdated', 'N/A'),
                            'CNAME': env.get('CNAME', 'N/A'),
                            'Tier': env.get('Tier', {}).get('Name', 'N/A'),
                            'InstanceCount': 0  # Will be updated below
                        }
                        
                        # Get instance count and other resource details
                        try:
                            resources = eb_client.describe_environment_resources(
                                EnvironmentName=env['EnvironmentName']
                            )
                            instances = resources['EnvironmentResources'].get('Instances', [])
                            env_details['InstanceCount'] = len(instances)
                        except ClientError as e:
                            console.print(f"[yellow]Warning: Could not get resources for {env['EnvironmentName']} in {region}: {str(e)}[/yellow]")
                        
                        # Get configuration settings
                        try:
                            config_response = eb_client.describe_configuration_settings(
                                ApplicationName=app['ApplicationName'],
                                EnvironmentName=env['EnvironmentName']
                            )
                            option_settings = config_response.get('ConfigurationSettings', [{}])[0].get('OptionSettings', [])
                            env_details['ConfigurationSettings'] = {
                                opt['OptionName']: opt['Value'] 
                                for opt in option_settings 
                                if 'Value' in opt
                            }
                        except ClientError as e:
                            console.print(f"[yellow]Warning: Could not get config settings for {env['EnvironmentName']} in {region}: {str(e)}[/yellow]")
                        
                        app_details['Environments'].append(env_details)
                
                except ClientError as e:
                    console.print(f"[yellow]Warning: Could not get environments for {app['ApplicationName']} in {region}: {str(e)}[/yellow]")
                
                all_applications[region].append(app_details)
                
        except ClientError as e:
            console.print(f"[yellow]Warning: Unexpected error processing {region}: {str(e)}[/yellow]")
    
    return all_applications

def display_results(applications):
    """Display detailed Elastic Beanstalk application information"""
    console = Console()
    
    for region, apps in applications.items():
        console.print(f"\n[bold cyan]Region: {region}[/bold cyan]")
        
        for app in apps:
            # Application Table
            app_table = Table(title=f"Application: {app['ApplicationName']}")
            app_table.add_column("Property", style="cyan")
            app_table.add_column("Value", style="magenta")
            
            app_table.add_row("Description", app['Description'])
            app_table.add_row("Date Created", str(app['DateCreated']))
            app_table.add_row("Date Updated", str(app['DateUpdated']))
            app_table.add_row("Configuration Templates", ", ".join(app['ConfigurationTemplates']) or "None")
            lifecycle = app['ResourceLifecycleConfig']
            app_table.add_row("Service Role", lifecycle.get('ServiceRole', 'N/A'))
            app_table.add_row("Version Lifecycle", str(lifecycle.get('VersionLifecycleConfig', 'N/A')))
            
            console.print(app_table)
            
            # Environments Table
            if app['Environments']:
                env_table = Table(title="Environments")
                env_table.add_column("Name", style="cyan")
                env_table.add_column("Status", style="green")
                env_table.add_column("Health", style="yellow")
                env_table.add_column("Version", style="magenta")
                env_table.add_column("Instances", style="blue")
                env_table.add_column("CNAME", style="white")
                
                for env in app['Environments']:
                    env_table.add_row(
                        env['EnvironmentName'],
                        env['Status'],
                        f"{env['Health']} ({env['HealthStatus']})",
                        env['VersionLabel'],
                        str(env['InstanceCount']),
                        env['CNAME']
                    )
                
                console.print(env_table)
                
                # Detailed Environment Information
                for env in app['Environments']:
                    detail_table = Table(title=f"Environment Details: {env['EnvironmentName']}")
                    detail_table.add_column("Property", style="cyan")
                    detail_table.add_column("Value", style="magenta")
                    
                    detail_table.add_row("Solution Stack", env['SolutionStackName'])
                    detail_table.add_row("Date Created", str(env['DateCreated']))
                    detail_table.add_row("Date Updated", str(env['DateUpdated']))
                    detail_table.add_row("Tier", env['Tier'])
                    
                    # Add some key configuration settings if available
                    if 'ConfigurationSettings' in env:
                        config = env['ConfigurationSettings']
                        detail_table.add_row("Instance Type", config.get('aws:autoscaling:launchconfiguration:InstanceType', 'N/A'))
                        detail_table.add_row("Min Instances", config.get('aws:autoscaling:asg:MinSize', 'N/A'))
                        detail_table.add_row("Max Instances", config.get('aws:autoscaling:asg:MaxSize', 'N/A'))
                        detail_table.add_row("Environment Type", config.get('aws:elasticbeanstalk:environment:EnvironmentType', 'N/A'))
                    
                    console.print(detail_table)
            
            console.print()  # Add spacing between applications

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Elastic Beanstalk Application Details Tool')
    parser.add_argument('--access-key', required=True, help='AWS Access Key (plain or base64 encoded)')
    parser.add_argument('--secret-key', required=True, help='AWS Secret Key (plain or base64 encoded)')
    parser.add_argument('--region', help='AWS Region to check (e.g., us-east-1)')
    parser.add_argument('--all-regions', action='store_true', help='Check all known AWS regions')
    args = parser.parse_args()
    
    # Decode keys
    access_key = decode_base64_key(args.access_key)
    secret_key = decode_base64_key(args.secret_key)
    
    # Determine regions to check
    if args.all_regions:
        regions = AWS_REGIONS
        action_msg = "all regions"
    elif args.region:
        regions = [args.region]
        action_msg = f"region {args.region}"
    else:
        parser.error("Either --region or --all-regions must be specified")
    
    console = Console()
    console.print(f"[bold green]Fetching Elastic Beanstalk Application Details for {action_msg}...[/bold green]")
    
    try:
        # Verify credentials first
        sts_client = boto3.client(
            'sts',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        identity = sts_client.get_caller_identity()
        console.print(f"[green]Authenticated as: {identity['Arn']}[/green]")
        
        applications = get_elasticbeanstalk_details(access_key, secret_key, regions)
        if not any(applications.values()):
            console.print(f"[yellow]No Elastic Beanstalk applications found in {action_msg}.[/yellow]")
        else:
            display_results(applications)
    except ClientError as e:
        console.print(f"[bold red]Authentication Error: {str(e)}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")

if __name__ == "__main__":
    main()
