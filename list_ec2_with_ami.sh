#!/bin/bash
# list_ec2_instances_with_ami.sh

# Check if region is provided as an argument
if [ -z "$1" ]; then
  echo "Usage: $0 <region>"
  echo "Example: $0 us-east-1"
  exit 1
fi

REGION="$1"

echo "Listing EC2 instances in region $REGION with AMI details..."

# Use AWS CLI to query EC2 instances
aws ec2 describe-instances \
  --region "$REGION" \
  --query 'Reservations[*].Instances[*].{
    InstanceId: InstanceId,
    State: State.Name,
    InstanceType: InstanceType,
    PublicIp: PublicIpAddress,
    PrivateIp: PrivateIpAddress,
    AMI: ImageId,
    LaunchTime: LaunchTime
  }' \
  --output table 2>/dev/null || {
    echo "Error: Failed to list instances. Check your AWS credentials, region, or permissions."
    exit 1
  }

echo "Instance listing completed."
