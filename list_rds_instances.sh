#!/bin/bash
# list_rds_instances.sh

REGION=$1

echo "Listing RDS Instances in $REGION..."
aws rds describe-db-instances \
  --region "$REGION" \
  --query "DBInstances[].{DBInstanceId:DBInstanceIdentifier, Engine:Engine, Status:DBInstanceStatus, Endpoint:Endpoint.Address}" \
  --output table 2>/dev/null || echo "No RDS instances found or access denied in $REGION"
