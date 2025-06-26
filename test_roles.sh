#!/bin/bash

# Script to list IAM roles that a specific principal might be allowed to assume

# Replace with the ARN of the principal (e.g., IAM user or role) tied to your key
#PRINCIPAL_ARN="arn:aws:iam::ACCOUNT_ID:user/YOUR_IAM_USER_NAME"

# Optional: Get the caller's identity to infer the principal if not provided
if [ -z "$PRINCIPAL_ARN" ]; then
  PRINCIPAL_ARN=$(aws sts get-caller-identity --query "Arn" --output text)
  echo "Using current caller identity: $PRINCIPAL_ARN"
fi

echo "Listing IAM roles that $PRINCIPAL_ARN might be allowed to assume..."
echo "---------------------------------------------------------"

# List all IAM roles
ROLES=$(aws iam list-roles --query "Roles[].{RoleName:RoleName,Arn:Arn}" --output text)

# Check each role's trust policy
while read -r ROLE_NAME ROLE_ARN; do
  # Get the trust policy document
  TRUST_POLICY=$(aws iam get-role --role-name "$ROLE_NAME" --query "Role.AssumeRolePolicyDocument" --output json 2>/dev/null)
  
  if [ -n "$TRUST_POLICY" ]; then
    # Check if the principal is listed in the trust policy
    PRINCIPAL_ALLOWED=$(echo "$TRUST_POLICY" | jq -r ".Statement[] | select(.Effect==\"Allow\" and .Action==\"sts:AssumeRole\" and (.Principal.AWS==\"$PRINCIPAL_ARN\" or .Principal.AWS[]?==\"$PRINCIPAL_ARN\"))")
    
    if [ -n "$PRINCIPAL_ALLOWED" ]; then
      echo "Role: $ROLE_NAME"
      echo "ARN: $ROLE_ARN"
      echo "Trust Policy allows $PRINCIPAL_ARN to assume this role."
      echo "---------------------------------------------------------"
    fi
  fi
done <<< "$ROLES"

echo "Enumeration complete!"
