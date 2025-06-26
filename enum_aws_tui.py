import boto3
import base64
from botocore.exceptions import ClientError
from rich.console import Console
from rich.table import Table
import argparse
import curses
import json

def decode_base64_key(encoded_key):
    """Decode base64 encoded key if necessary"""
    try:
        return base64.b64decode(encoded_key).decode('utf-8')
    except:
        return encoded_key

def get_user_id(access_key, secret_key):
    """Get AWS user ID using the provided credentials"""
    try:
        sts_client = boto3.client('sts', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
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
    """Check basic permissions for common AWS services"""
    permissions = {}
    services_to_test = {
        's3': ['ListBuckets'],
        'ec2': ['DescribeInstances'],
        'iam': ['ListUsers'],
        'lambda': ['ListFunctions'],
        'dynamodb': ['ListTables']
    }
    
    regions = get_all_regions() if all_regions else [None]
    
    for service, actions in services_to_test.items():
        service_permissions = {}
        if service in ['s3', 'iam']:
            regions = [None]
            
        for region in regions:
            try:
                client = boto3.client(service, aws_access_key_id=access_key, 
                                   aws_secret_access_key=secret_key, region_name=region)
                allowed_actions = []
                for action in actions:
                    try:
                        if service == 's3' and action == 'ListBuckets':
                            client.list_buckets()
                            allowed_actions.append(action)
                        elif service == 'ec2' and action == 'DescribeInstances':
                            client.describe_instances(MaxResults=5)
                            allowed_actions.append(action)
                        elif service == 'iam' and action == 'ListUsers':
                            client.list_users(MaxItems=1)
                            allowed_actions.append(action)
                        elif service == 'lambda' and action == 'ListFunctions':
                            client.list_functions(MaxItems=1)
                            allowed_actions.append(action)
                        elif service == 'dynamodb' and action == 'ListTables':
                            client.list_tables(Limit=1)
                            allowed_actions.append(action)
                    except ClientError:
                        continue
                
                key = f"{service} ({region})" if region else service
                service_permissions[key] = allowed_actions if allowed_actions else ["None"]
            except ClientError:
                key = f"{service} ({region})" if region else service
                service_permissions[key] = ["Access Denied"]
        
        permissions.update(service_permissions)
    
    return permissions

def perform_action(access_key, secret_key, service_region, action):
    """Perform the selected allowed action and return results"""
    console = Console()
    try:
        # Split service and region if region is present
        if '(' in service_region:
            service, region = service_region.split(' (')
            region = region.rstrip(')')
        else:
            service, region = service_region, None
            
        client = boto3.client(service, aws_access_key_id=access_key, 
                            aws_secret_access_key=secret_key, region_name=region)
        
        if service == 's3' and action == 'ListBuckets':
            result = client.list_buckets()
            return json.dumps(result['Buckets'], indent=2, default=str)
        elif service == 'ec2' and action == 'DescribeInstances':
            result = client.describe_instances(MaxResults=5)
            return json.dumps(result['Reservations'], indent=2, default=str)
        elif service == 'iam' and action == 'ListUsers':
            result = client.list_users(MaxItems=10)
            return json.dumps(result['Users'], indent=2, default=str)
        elif service == 'lambda' and action == 'ListFunctions':
            result = client.list_functions(MaxItems=10)
            return json.dumps(result['Functions'], indent=2, default=str)
        elif service == 'dynamodb' and action == 'ListTables':
            result = client.list_tables(Limit=10)
            return json.dumps(result['TableNames'], indent=2, default=str)
        else:
            return "Action not implemented"
    except ClientError as e:
        return f"Error performing action: {str(e)}"

def curses_menu(stdscr, permissions, access_key, secret_key):
    """Display interactive menu using curses"""
    curses.curs_set(0)  # Hide cursor
    current_row = 0
    
    # Create menu items from permissions
    menu_items = []
    for service_region, actions in permissions.items():
        if actions[0] not in ["None", "Access Denied"]:
            for action in actions:
                menu_items.append((service_region, action))
    
    if not menu_items:
        stdscr.addstr(0, 0, "No allowed actions found. Press any key to exit.")
        stdscr.refresh()
        stdscr.getch()
        return

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # Display title
        title = "Select an action to perform (Use arrow keys, Enter to select, Q to quit)"
        stdscr.addstr(0, 0, title[:width-1])
        
        # Display menu items
        for idx, (service_region, action) in enumerate(menu_items):
            x = 0
            y = idx + 2
            if y >= height - 1:
                break
            if idx == current_row:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(y, x, f"{service_region}: {action}"[:width-1])
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(y, x, f"{service_region}: {action}"[:width-1])
        
        stdscr.refresh()
        key = stdscr.getch()
        
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu_items) - 1:
            current_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            stdscr.clear()
            service_region, action = menu_items[current_row]
            result = perform_action(access_key, secret_key, service_region, action)
            # Display result
            lines = result.split('\n')
            for i, line in enumerate(lines):
                if i >= height - 1:
                    break
                stdscr.addstr(i, 0, line[:width-1])
            stdscr.addstr(height-1, 0, "Press any key to continue..."[:width-1])
            stdscr.refresh()
            stdscr.getch()
        elif key == ord('q') or key == ord('Q'):
            break

def display_results(user_id, arn, permissions, access_key, secret_key):
    """Display results and launch menu"""
    console = Console()
    console.print(f"[bold green]User ID:[/bold green] {user_id}")
    console.print(f"[bold green]ARN:[/bold green] {arn}")
    console.print()
    
    table = Table(title="AWS Service Permissions")
    table.add_column("Service/Region", style="cyan", no_wrap=True)
    table.add_column("Allowed Actions", style="magenta")
    
    for service_region, actions in permissions.items():
        table.add_row(service_region.upper(), ", ".join(actions))
    
    console.print(table)
    console.print("\nLaunching interactive menu...")
    
    # Launch curses menu
    curses.wrapper(curses_menu, permissions, access_key, secret_key)

def main():
    parser = argparse.ArgumentParser(description='AWS Key Enumeration Tool')
    parser.add_argument('--access-key', required=True, help='AWS Access Key (plain or base64 encoded)')
    parser.add_argument('--secret-key', required=True, help='AWS Secret Key (plain or base64 encoded)')
    parser.add_argument('--all-regions', action='store_true', help='Check permissions across all regions')
    args = parser.parse_args()
    
    access_key = decode_base64_key(args.access_key)
    secret_key = decode_base64_key(args.secret_key)
    
    user_id, arn = get_user_id(access_key, secret_key)
    
    if user_id:
        permissions = check_service_permissions(access_key, secret_key, args.all_regions)
        display_results(user_id, arn, permissions, access_key, secret_key)
    else:
        console = Console()
        console.print(f"[bold red]Failed to authenticate: {arn}[/bold red]")

if __name__ == "__main__":
    main()
