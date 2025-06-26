#!/bin/bash

# Script to list all EKS clusters and Secrets Manager secrets across all regions

# Get all AWS regions
REGIONS=$(aws ec2 describe-regions --query "Regions[].RegionName" --output text)

echo "=== Listing All EKS Clusters Across All Regions ==="
echo "---------------------------------------------------------"

# Loop through each region to list EKS clusters
for REGION in $REGIONS; do
  echo "Checking EKS clusters in region: $REGION"
  CLUSTERS=$(aws eks list-clusters \
    --region "$REGION" \
    --query "clusters[]" \
    --output table 2>/dev/null)
  
  if [ -n "$CLUSTERS" ] && [ "$CLUSTERS" != "||" ]; then
    echo "$CLUSTERS"
  else
    echo "No EKS clusters found in $REGION"
  fi
  echo "---------------------------------------------------------"
done

echo "=== Listing All Secrets Manager Secrets ==="
echo "---------------------------------------------------------"

# List secrets in each region (Secrets Manager is region-specific)
for REGION in $REGIONS; do
  echo "Checking Secrets Manager secrets in region: $REGION"
  SECRETS=$(aws secretsmanager list-secrets \
    --region "$REGION" \
    --query "SecretList[].{Name:Name, ARN:ARN, LastChangedDate:LastChangedDate}" \
    --output table 2>/dev/null)
  
  if [ -n "$SECRETS" ] && [ "$SECRETS" != "||" ]; then
    echo "$SECRETS"
  else
    echo "No secrets found in $REGION"
  fi
  echo "---------------------------------------------------------"
done

echo "Enumeration complete!"
