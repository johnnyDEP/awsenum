import boto3
import base64
from botocore.exceptions import ClientError
from rich.console import Console
from rich.table import Table
import argparse
import csv

def decode_base64_key(encoded_key):
    """Decode base64 encoded key if necessary and return both versions"""
    try:
        decoded = base64.b64decode(encoded_key).decode('utf-8')
        return decoded, encoded_key
    except:
        return encoded_key, encoded_key  # Return original as both if not base64 encoded

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

def get_all_regions():
    """Get list of all available AWS regions"""
    ec2_client = boto3.client('ec2')
    regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
    return regions

def check_service_permissions(access_key, secret_key, all_regions=False):
    """Check basic permissions for AWS services across regions if specified"""
    permissions = {}
    
    services_to_test = {
        's3': ['ListBuckets'],
        'iam': ['ListUsers'],
        'route53': ['ListHostedZones'],
        'cloudfront': ['ListDistributions'],
        'ec2': ['DescribeInstances', 'DescribeVolumes'],
        'lambda': ['ListFunctions'],
        'dynamodb': ['ListTables'],
        'rds': ['DescribeDBInstances'],
        'sns': ['ListTopics'],
        'sqs': ['ListQueues'],
        'ecs': ['ListClusters'],
        'eks': ['ListClusters'],
        'elasticbeanstalk': ['ListApplications'],
        'cloudwatch': ['ListMetrics'],
        'autoscaling': ['DescribeAutoScalingGroups'],
        'elb': ['DescribeLoadBalancers'],
        'elbv2': ['DescribeLoadBalancers'],
        'kms': ['ListKeys'],
        'secretsmanager': ['ListSecrets'],
        'ssm': ['ListDocuments'],
        'stepfunctions': ['ListStateMachines'],
        'glue': ['GetDatabases'],
        'athena': ['ListWorkGroups'],
        'redshift': ['DescribeClusters'],
        'cloudformation': ['ListStacks']
    }
    
    regions = get_all_regions() if all_regions else [None]
    
    for service, actions in services_to_test.items():
        service_permissions = {}
        global_services = ['s3', 'iam', 'route53', 'cloudfront']
        if service in global_services:
            regions = [None]
            
        for region in regions:
            try:
                client = boto3.client(
                    service,
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=region
                )
                
                allowed_actions = []
                for action in actions:
                    try:
                        if service == 's3' and action == 'ListBuckets':
                            client.list_buckets()
                        elif service == 'iam' and action == 'ListUsers':
                            client.list_users(MaxItems=1)
                        elif service == 'route53' and action == 'ListHostedZones':
                            client.list_hosted_zones(MaxItems='1')
                        elif service == 'cloudfront' and action == 'ListDistributions':
                            client.list_distributions(MaxItems='1')
                        elif service == 'ec2' and action == 'DescribeInstances':
                            client.describe_instances(MaxResults=5)
                        elif service == 'ec2' and action == 'DescribeVolumes':
                            client.describe_volumes(MaxResults=5)
                        elif service == 'lambda' and action == 'ListFunctions':
                            client.list_functions(MaxItems=1)
                        elif service == 'dynamodb' and action == 'ListTables':
                            client.list_tables(Limit=1)
                        elif service == 'rds' and action == 'DescribeDBInstances':
                            client.describe_db_instances()
                        elif service == 'sns' and action == 'ListTopics':
                            client.list_topics()
                        elif service == 'sqs' and action == 'ListQueues':
                            client.list_queues()
                        elif service == 'ecs' and action == 'ListClusters':
                            client.list_clusters()
                        elif service == 'eks' and action == 'ListClusters':
                            client.list_clusters()
                        elif service == 'elasticbeanstalk' and action == 'ListApplications':
                            client.describe_applications()
                        elif service == 'cloudwatch' and action == 'ListMetrics':
                            client.list_metrics()
                        elif service == 'autoscaling' and action == 'DescribeAutoScalingGroups':
                            client.describe_auto_scaling_groups(MaxRecords=1)
                        elif service == 'elb' and action == 'DescribeLoadBalancers':
                            client.describe_load_balancers(PageSize=1)
                        elif service == 'elbv2' and action == 'DescribeLoadBalancers':
                            client.describe_load_balancers(PageSize=1)
                        elif service == 'kms' and action == 'ListKeys':
                            client.list_keys(Limit=1)
                        elif service == 'secretsmanager' and action == 'ListSecrets':
                            client.list_secrets(MaxResults=1)
                        elif service == 'ssm' and action == 'ListDocuments':
                            client.list_documents(MaxResults=1)
                        elif service == 'stepfunctions' and action == 'ListStateMachines':
                            client.list_state_machines(maxResults=1)
                        elif service == 'glue' and action == 'GetDatabases':
                            client.get_databases()
                        elif service == 'athena' and action == 'ListWorkGroups':
                            client.list_work_groups()
                        elif service == 'redshift' and action == 'DescribeClusters':
                            client.describe_clusters(MaxRecords=20)
                        elif service == 'cloudformation' and action == 'ListStacks':
                            client.list_stacks()
                        
                        allowed_actions.append(action)
                    except ClientError:
                        continue
                
                if region:
                    service_permissions[f"{service} ({region})"] = allowed_actions if allowed_actions else ["None"]
                else:
                    service_permissions[service] = allowed_actions if allowed_actions else ["None"]
            except ClientError:
                if region:
                    service_permissions[f"{service} ({region})"] = ["Access Denied"]
                else:
                    service_permissions[service] = ["Access Denied"]
        
        permissions.update(service_permissions)
    
    return permissions

def display_results(user_id, arn, permissions, access_key_decoded, access_key_encoded, 
                   secret_key_decoded, secret_key_encoded):
    """Display results in a rich table format including encoded/decoded keys"""
    console = Console()
    
    # Display user info
    console.print(f"[bold green]User ID:[/bold green] {user_id}")
    console.print(f"[bold green]ARN:[/bold green] {arn}")
    console.print()
    
    # Create permissions table with key information
    table = Table(title="AWS Service Permissions")
    table.add_column("Service/Region", style="cyan", no_wrap=True)
    table.add_column("Allowed Actions", style="magenta")
    
    # Add key information as first two rows
    table.add_row("ACCESS KEY (BASE64)", access_key_encoded)
    table.add_row("ACCESS KEY (DECODED)", access_key_decoded)
    table.add_row("SECRET KEY (BASE64)", secret_key_encoded)
    table.add_row("SECRET KEY (DECODED)", secret_key_decoded)
    table.add_row("", "")  # Empty row for separation
    
    # Add service permissions
    for service_region, actions in permissions.items():
        table.add_row(service_region.upper(), ", ".join(actions))
    
    console.print(table)

def process_credentials(access_key_input, secret_key_input, all_regions):
    """Process a single set of credentials"""
    # Get both decoded and encoded versions
    access_key_decoded, access_key_encoded = decode_base64_key(access_key_input.strip())
    secret_key_decoded, secret_key_encoded = decode_base64_key(secret_key_input.strip())
    
    user_id, arn = get_user_id(access_key_decoded, secret_key_decoded)
    
    console = Console()
    if user_id:
        console.print(f"\n[bold blue]Processing credentials: {access_key_decoded[:6]}...[/bold blue]")
        permissions = check_service_permissions(access_key_decoded, secret_key_decoded, all_regions)
        display_results(user_id, arn, permissions, 
                       access_key_decoded, access_key_encoded,
                       secret_key_decoded, secret_key_encoded)
    else:
        console.print(f"\n[bold red]Failed to authenticate with {access_key_decoded[:6]}...: {arn}[/bold red]")

def main():
    parser = argparse.ArgumentParser(description='AWS Key Enumeration Tool')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--access-key', help='AWS Access Key (plain or base64 encoded)')
    group.add_argument('--file', help='File containing comma-separated access_key,secret_key pairs')
    parser.add_argument('--secret-key', help='AWS Secret Key (plain or base64 encoded)')
    parser.add_argument('--all-regions', action='store_true', help='Check permissions across all regions')
    args = parser.parse_args()
    
    if args.file:
        try:
            with open(args.file, 'r') as f:
                csv_reader = csv.reader(f)
                for row in csv_reader:
                    if len(row) != 2:
                        console = Console()
                        console.print(f"[bold red]Invalid format in file: {row}. Expected: access_key,secret_key[/bold red]")
                        continue
                    access_key, secret_key = row
                    process_credentials(access_key, secret_key, args.all_regions)
        except FileNotFoundError:
            console = Console()
            console.print(f"[bold red]File not found: {args.file}[/bold red]")
        except Exception as e:
            console = Console()
            console.print(f"[bold red]Error reading file: {str(e)}[/bold red]")
    else:
        if not args.secret_key:
            parser.error("--secret-key is required when using --access-key")
        process_credentials(args.access_key, args.secret_key, args.all_regions)

if __name__ == "__main__":
    main()
