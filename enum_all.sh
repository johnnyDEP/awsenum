#!/bin/bash

# Main script to enumerate AWS resources across all regions

# Get all AWS regions
REGIONS=$(aws ec2 describe-regions --query "Regions[].RegionName" --output text --profile account_903894642427)

echo "Starting enumeration of AWS resources across all regions..."
echo "---------------------------------------------------------"

# Loop through each region and call individual service scripts
for REGION in $REGIONS; do
  echo "Processing region: $REGION"
  ./list_ec2_instances.sh "$REGION"
  ./list_s3_buckets.sh "$REGION"
  ./list_rds_instances.sh "$REGION"
  ./list_elasticache_redis.sh "$REGION"
  ./list_lambda_functions.sh "$REGION"
  echo "---------------------------------------------------------"
done

echo "Enumeration complete!"
