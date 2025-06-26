#!/bin/bash

# Script to simulate a wide range of AWS permissions for a principal

# Replace with the ARN of the principal (e.g., IAM user or role)
#PRINCIPAL_ARN="arn:aws:iam::ACCOUNT_ID:user/IAM_USER_NAME"

# Optional: Infer the principal ARN from the current caller identity if not set
if [ -z "$PRINCIPAL_ARN" ]; then
  PRINCIPAL_ARN=$(aws sts get-caller-identity --query "Arn" --output text)
  echo "Using current caller identity: $PRINCIPAL_ARN"
fi

# Default region for resource ARNs (modify as needed)
REGION="us-east-1"

# Replace with your AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)

echo "Simulating permissions for $PRINCIPAL_ARN..."
echo "---------------------------------------------------------"

# List of AWS actions to test (expandable)
ACTIONS=(
  # EC2 Actions
  "ec2:StartInstances" "ec2:StopInstances" "ec2:TerminateInstances" "ec2:DescribeInstances" "ec2:RunInstances" "ec2:CreateSnapshot" "ec2:DescribeSnapshots" "ec2:AttachVolume"
  # S3 Actions
  "s3:ListAllMyBuckets" "s3:GetObject" "s3:PutObject" "s3:DeleteObject" "s3:CreateBucket"
  # IAM Actions
  "iam:CreateUser" "iam:DeleteUser" "iam:CreateRole" "iam:AttachUserPolicy" "iam:GetAccountSummary"
  # RDS Actions
  "rds:CreateDBInstance" "rds:DeleteDBInstance" "rds:DescribeDBInstances"
  # Lambda Actions
  "lambda:CreateFunction" "lambda:InvokeFunction" "lambda:ListFunctions"
  # EKS Actions
  "eks:CreateCluster" "eks:DeleteCluster" "eks:ListClusters"
  # Secrets Manager Actions
  "secretsmanager:CreateSecret" "secretsmanager:GetSecretValue" "secretsmanager:ListSecrets"
  # General STS Action
  "sts:AssumeRole"
)

# Function to simulate a single action
simulate_action() {
  local action=$1
  local resource="arn:aws:${action%%:*}:$REGION:$ACCOUNT_ID:*"  # Wildcard resource ARN

  # Adjust resource ARN for specific services
  case $action in
    s3:*)
      resource="arn:aws:s3:::*"  # S3 uses a different ARN format
      ;;
    iam:*)
      resource="*"  # IAM often uses wildcard for resource-level permissions
      ;;
    sts:AssumeRole)
      resource="arn:aws:iam::$ACCOUNT_ID:role/*"  # Role ARN for AssumeRole
      ;;
  esac

  echo "Testing $action on $resource..."
  RESULT=$(aws iam simulate-principal-policy \
    --policy-source-arn "$PRINCIPAL_ARN" \
    --action-names "$action" \
    --resource-arns "$resource" \
    --output json 2>/dev/null)

  DECISION=$(echo "$RESULT" | jq -r '.EvaluationResults[0].EvalDecision')
  if [ "$DECISION" = "allowed" ]; then
    echo "ALLOWED: $action"
  elif [ "$DECISION" = "implicitDeny" ] || [ "$DECISION" = "explicitDeny" ]; then
    echo "DENIED: $action"
  else
    echo "UNKNOWN ($DECISION): $action"
  fi
  echo "---------------------------------------------------------"
}

# Iterate over all actions and simulate permissions
for ACTION in "${ACTIONS[@]}"; do
  simulate_action "$ACTION"
done

echo "Simulation complete!"
