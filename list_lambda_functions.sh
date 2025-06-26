#!/bin/bash
# list_lambda_functions.sh

REGION=$1

echo "Listing Lambda Functions in $REGION..."
aws lambda list-functions \
  --region "$REGION" \
  --query "Functions[].{FunctionName:FunctionName, Runtime:Runtime, LastModified:LastModified}" \
  --output table 2>/dev/null || echo "No Lambda functions found or access denied in $REGION"
