#!/bin/bash
# list_ec2_amis.sh

# Check if region is provided as an argument
if [ -z "$1" ]; then
  echo "Usage: $0 <region>"
  echo "Example: $0 us-east-1"
  exit 1
fi

REGION="$1"

echo "Listing AMI images in region $REGION..."

# Query AMIs owned by Amazon or AWS Marketplace
aws ec2 describe-images \
  --region "$REGION" \
  --owners amazon aws-marketplace \
  --filters "Name=state,Values=available" \
  --query 'Images[*].{
    ImageId: ImageId,
    Name: Name,
    Description: Description,
    CreationDate: CreationDate,
    Architecture: Architecture,
    RootDeviceType: RootDeviceType
  }' \
  --output table 2>/dev/null || {
    echo "Error: Failed to list AMIs. Check your AWS credentials, region, or permissions."
    exit 1
  }

echo "AMI listing completed."
