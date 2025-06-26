import boto3
import time
from botocore.exceptions import ClientError

# Hardcoded SSH public key (replace with your actual public key)
SSH_PUBLIC_KEY = "ssh-rsa blahpub.pub"

# Function to list available AWS regions
def list_regions():
    ec2_client = boto3.client('ec2')  # Temporary client to fetch regions
    response = ec2_client.describe_regions()
    return [region['RegionName'] for region in response['Regions']]

# Function to select a region
def select_region():
    regions = list_regions()
    print("\n=== Available AWS Regions ===")
    for i, region in enumerate(regions, 1):
        print(f"{i}. {region}")
    while True:
        try:
            choice = int(input("Select a region by number: ")) - 1
            if 0 <= choice < len(regions):
                return regions[choice]
            else:
                print("Invalid selection. Please choose a valid number.")
        except ValueError:
            print("Please enter a valid number.")

# Function to list running EC2 instances
def list_running_instances(ec2_client):
    instances = ec2_client.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )['Reservations']
    return [instance for reservation in instances for instance in reservation['Instances']]

# Function to create a snapshot from an instance's volume
def create_snapshot(instance_id, ec2_resource):
    instance = ec2_resource.Instance(instance_id)
    volume = list(instance.volumes.all())[0]  # Assuming one root volume
    print(f"Creating snapshot of volume {volume.id} from instance {instance_id}...")
    snapshot = volume.create_snapshot(Description=f"Snapshot of {instance_id}")
    snapshot.wait_until_completed()
    print(f"Snapshot {snapshot.id} created successfully.")
    return snapshot.id

# Function to create a new instance with the SSH key
def create_new_instance(snapshot_id, ec2_client, ec2_resource):
    # Create a key pair with the hardcoded public key
    key_name = f"temp-key-{int(time.time())}"
    try:
        ec2_client.import_key_pair(KeyName=key_name, PublicKeyMaterial=SSH_PUBLIC_KEY)
        print(f"Imported key pair: {key_name}")
    except ClientError as e:
        if "InvalidKeyPair.Duplicate" in str(e):
            print(f"Key pair {key_name} already exists, reusing it.")
        else:
            raise e

    # Launch a new instance (using a default AMI, t2.micro type)
    response = ec2_client.run_instances(
        ImageId='ami-02c78647b95a018b6',  # Ubuntu 22.04 LTS Minimal
        InstanceType='t2.micro',
        KeyName=key_name,
        MinCount=1,
        MaxCount=1,
        TagSpecifications=[{
            'ResourceType': 'instance',
            'Tags': [{'Key': 'Name', 'Value': 'SnapshotClone'}]
        }]
    )
    new_instance_id = response['Instances'][0]['InstanceId']
    print(f"Launching new instance {new_instance_id}...")
    
    # Wait for the instance to be running
    waiter = ec2_client.get_waiter('instance_running')
    waiter.wait(InstanceIds=[new_instance_id])
    print(f"New instance {new_instance_id} is running.")
    return new_instance_id

# Function to attach the snapshot as a volume to the new instance
def attach_snapshot_to_instance(snapshot_id, new_instance_id, ec2_client, ec2_resource):
    # Create a volume from the snapshot
    volume = ec2_client.create_volume(
        SnapshotId=snapshot_id,
        AvailabilityZone=ec2_resource.Instance(new_instance_id).placement['AvailabilityZone']
    )
    volume_id = volume['VolumeId']
    print(f"Created volume {volume_id} from snapshot {snapshot_id}...")
    
    # Wait for the volume to be available
    waiter = ec2_client.get_waiter('volume_available')
    waiter.wait(VolumeIds=[volume_id])
    
    # Attach the volume to the new instance
    ec2_client.attach_volume(
        VolumeId=volume_id,
        InstanceId=new_instance_id,
        Device='/dev/xvdf'  # Device name may need adjustment based on OS
    )
    print(f"Volume {volume_id} attached to instance {new_instance_id} as /dev/xvdf.")

# Main menu function
def main_menu(ec2_client, ec2_resource):
    selected_instance = None
    snapshot_id = None
    new_instance_id = None

    while True:
        print("\n=== EC2 Instance Management Menu ===")
        print("1. List and select a running EC2 instance")
        print("2. Create a snapshot of the selected instance")
        print("3. Create a new instance with SSH key")
        print("4. Attach snapshot to the new instance")
        print("5. Exit")
        choice = input("Enter your choice (1-5): ")

        if choice == '1':
            instances = list_running_instances(ec2_client)
            if not instances:
                print("No running instances found in this region.")
                continue
            print("\nRunning Instances:")
            for i, inst in enumerate(instances, 1):
                name = next((tag['Value'] for tag in inst.get('Tags', []) if tag['Key'] == 'Name'), 'Unnamed')
                print(f"{i}. {inst['InstanceId']} - {name} ({inst['InstanceType']})")
            try:
                selection = int(input("Select an instance by number: ")) - 1
                if 0 <= selection < len(instances):
                    selected_instance = instances[selection]['InstanceId']
                    print(f"Selected instance: {selected_instance}")
                else:
                    print("Invalid selection.")
            except ValueError:
                print("Please enter a valid number.")

        elif choice == '2':
            if not selected_instance:
                print("Please select an instance first (Option 1).")
                continue
            confirm = input(f"Create snapshot for {selected_instance}? (y/n): ")
            if confirm.lower() == 'y':
                snapshot_id = create_snapshot(selected_instance, ec2_resource)

        elif choice == '3':
            if not snapshot_id:
                print("Please create a snapshot first (Option 2).")
                continue
            confirm = input("Create a new instance with SSH key? (y/n): ")
            if confirm.lower() == 'y':
                new_instance_id = create_new_instance(snapshot_id, ec2_client, ec2_resource)

        elif choice == '4':
            if not new_instance_id:
                print("Please create a new instance first (Option 3).")
                continue
            print(f"Current snapshot ID: {snapshot_id if snapshot_id else 'None'}")
            use_current = input("Use the current snapshot ID (if available) or enter a new one? (y for current, n for new): ")
            if use_current.lower() == 'y' and snapshot_id:
                attach_snap_id = snapshot_id
            else:
                attach_snap_id = input("Enter the snapshot ID to attach (e.g., snap-0123456789abcdef0): ").strip()
                if not attach_snap_id.startswith('snap-'):
                    print("Invalid snapshot ID format. It should start with 'snap-'.")
                    continue
            
            confirm = input(f"Attach snapshot {attach_snap_id} to {new_instance_id}? (y/n): ")
            if confirm.lower() == 'y':
                try:
                    attach_snapshot_to_instance(attach_snap_id, new_instance_id, ec2_client, ec2_resource)
                except ClientError as e:
                    print(f"Error attaching snapshot: {e}")

        elif choice == '5':
            print("Exiting...")
            break

        else:
            print("Invalid choice. Please select 1-5.")

if __name__ == "__main__":
    try:
        # Select region first
        selected_region = select_region()
        print(f"Selected region: {selected_region}")

        # Initialize EC2 client and resource with the selected region
        ec2_client = boto3.client('ec2', region_name=selected_region)
        ec2_resource = boto3.resource('ec2', region_name=selected_region)

        # Start the main menu
        main_menu(ec2_client, ec2_resource)
    except Exception as e:
        print(f"An error occurred: {e}")
