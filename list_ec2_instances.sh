#!/bin/bash
# list_ec2_instances.sh

REGION=$1

echo "Listing EC2 Instances in $REGION..."
aws ec2 describe-instances \
  --region "$REGION" \
  --query "Reservations[].Instances[].{InstanceId:InstanceId, State:State.Name, Type:InstanceType, PublicIp:PublicIpAddress}" \
  --output table 2>/dev/null || echo "No EC2 instances found or access denied in $REGION"
