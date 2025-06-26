# AWS Enumeration Tools

This repository contains a collection of tools for enumerating and analyzing AWS resources and permissions. Below is a detailed description of each script and its usage.

## Python Scripts

### aws_takeover.py
An interactive EC2 instance management tool that allows you to create snapshots of running instances and launch new instances with custom SSH access.

**Features:**
- List and select running EC2 instances
- Create snapshots of selected instances
- Launch new instances with custom SSH keys
- Attach snapshots to new instances
- Interactive menu-driven interface

**Usage:**
```bash
python aws_takeover.py
```

**Workflow:**
1. Select an AWS region from the available list
2. Use the interactive menu to:
   - List and select a running EC2 instance
   - Create a snapshot of the selected instance
   - Launch a new instance with SSH access
   - Attach the snapshot to the new instance

**Screenshot:**
![AWS Takeover Tool Interface](screenshots/awstakeover_1.png)

**Example Session:**
```bash
$ python aws_takeover.py

=== Available AWS Regions ===
1. us-east-1
2. us-west-2
3. eu-west-1
...
Select a region by number: 1

=== EC2 Instance Management Menu ===
1. List and select a running EC2 instance
2. Create a snapshot of the selected instance
3. Create a new instance with SSH key
4. Attach snapshot to the new instance
5. Exit
Enter your choice (1-5): 1

Running Instances:
1. i-1234567890abcdef0 - WebServer (t2.micro)
2. i-0987654321fedcba0 - Database (t2.small)
Select an instance by number: 1
Selected instance: i-1234567890abcdef0

=== EC2 Instance Management Menu ===
...
Enter your choice (1-5): 2
Create snapshot for i-1234567890abcdef0? (y/n): y
Creating snapshot of volume vol-1234567890abcdef0 from instance i-1234567890abcdef0...
Snapshot snap-1234567890abcdef0 created successfully.
```

**Note:** Before using this script, you need to:
1. Configure your AWS credentials
2. Replace the `SSH_PUBLIC_KEY` variable in the script with your actual SSH public key
3. Ensure you have the necessary AWS permissions for EC2 operations

### enum_aws.py
A comprehensive AWS permissions enumeration tool that checks access to various AWS services.

**Usage:**
```bash
python enum_aws.py --access-key ACCESS_KEY --secret-key SECRET_KEY [--all-regions]
# OR
python enum_aws.py --file credentials.csv [--all-regions]
```

**Parameters:**
- `--access-key`: AWS Access Key (can be plain or base64 encoded)
- `--secret-key`: AWS Secret Key (can be plain or base64 encoded)
- `--file`: Path to a CSV file containing access_key,secret_key pairs
- `--all-regions`: Optional flag to check permissions across all AWS regions

**Screenshot:**
![AWS Enumeration Tool Interface](screenshots/enum_aws.png)

**Example:**
```bash
python enum_aws.py --access-key AKIAXXXXXXXXXXXXXXXX --secret-key xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx --all-regions
```

### enum_aws_tui.py
Interactive terminal user interface for AWS enumeration.

**Usage:**
```bash
python enum_aws_tui.py
```

### enum_ec2.py
EC2 instance enumeration tool.

**Usage:**
```bash
python enum_ec2.py --profile PROFILE_NAME [--region REGION]
```

**Parameters:**
- `--profile`: AWS profile name to use
- `--region`: Optional AWS region to target

**Screenshot:**
![EC2 Enumeration Tool Interface](screenshots/enum_ec2.png)

### enum_elasticbean.py
Elastic Beanstalk environment enumeration tool.

**Usage:**
```bash
python enum_elasticbean.py --profile PROFILE_NAME [--region REGION]
```

**Parameters:**
- `--profile`: AWS profile name to use
- `--region`: Optional AWS region to target

### list_bucket_contents.py
Lists contents of an S3 bucket.

**Usage:**
```bash
python list_bucket_contents.py --bucket BUCKET_NAME [--profile PROFILE_NAME]
```

**Parameters:**
- `--bucket`: Name of the S3 bucket to list
- `--profile`: Optional AWS profile name to use

### list_buckets.py
Lists all S3 buckets in an AWS account.

**Usage:**
```bash
python list_buckets.py --profile PROFILE_NAME
```

**Parameters:**
- `--profile`: AWS profile name to use

**Screenshot:**
![S3 Buckets List Interface](screenshots/list_buckets.png)

## Shell Scripts

### enum_all.sh
Master script that runs all enumeration scripts across all AWS regions.

**Usage:**
```bash
./enum_all.sh
```

### check_aws.sh
Checks AWS credentials and basic connectivity.

**Usage:**
```bash
./check_aws.sh [PROFILE_NAME]
```

**Parameters:**
- `PROFILE_NAME`: Optional AWS profile name to use

### list_ec2_instances.sh
Lists EC2 instances in a specific region.

**Usage:**
```bash
./list_ec2_instances.sh [REGION]
```

**Parameters:**
- `REGION`: Optional AWS region to target

### list_rds_instances.sh
Lists RDS instances in a specific region.

**Usage:**
```bash
./list_rds_instances.sh [REGION]
```

**Parameters:**
- `REGION`: Optional AWS region to target

### list_s3_buckets.sh
Lists S3 buckets in a specific region.

**Usage:**
```bash
./list_s3_buckets.sh [REGION]
```

**Parameters:**
- `REGION`: Optional AWS region to target

### role_simulation.sh
Simulates AWS IAM role permissions.

**Usage:**
```bash
./role_simulation.sh ROLE_ARN [PROFILE_NAME]
```

**Parameters:**
- `ROLE_ARN`: ARN of the IAM role to simulate
- `PROFILE_NAME`: Optional AWS profile name to use

### swap_profile.sh
Switches between AWS profiles.

**Usage:**
```bash
./swap_profile.sh PROFILE_NAME
```

**Parameters:**
- `PROFILE_NAME`: AWS profile name to switch to

### test_roles.sh
Tests IAM role permissions.

**Usage:**
```bash
./test_roles.sh [PROFILE_NAME]
```

**Parameters:**
- `PROFILE_NAME`: Optional AWS profile name to use

### update_aws_credentials.sh
Updates AWS credentials in the credentials file.

**Usage:**
```bash
./update_aws_credentials.sh PROFILE_NAME ACCESS_KEY SECRET_KEY
```

**Parameters:**
- `PROFILE_NAME`: AWS profile name to update
- `ACCESS_KEY`: New AWS access key
- `SECRET_KEY`: New AWS secret key

## Prerequisites

- AWS CLI installed and configured
- Python 3.x
- Required Python packages:
  - boto3
  - rich
  - argparse

## Installation

1. Clone the repository:
```bash
git clone https://github.com/johnnyDEP/awsenum.git
cd awsenum
```

2. Install required Python packages:
```bash
pip install -r requirements.txt
```

3. Make shell scripts executable:
```bash
chmod +x *.sh
```

## Security Note

These tools are designed for security assessment and enumeration purposes. Always ensure you have proper authorization before using these tools against any AWS environment.
