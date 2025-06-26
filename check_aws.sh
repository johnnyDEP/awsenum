#!/bin/bash

# Check if base64 encoded credentials are provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <base64_encoded_access_key> <base64_encoded_secret_key>"
    exit 1
fi

# Decode the credentials
ACCESS_KEY=$(echo "$1" | base64 -d)
SECRET_KEY=$(echo "$2" | base64 -d)

# Configure AWS credentials
aws configure set aws_access_key_id "$ACCESS_KEY" --profile temp_profile
aws configure set aws_secret_access_key "$SECRET_KEY" --profile temp_profile
aws configure set region us-east-1 --profile temp_profile

# Get caller identity
IDENTITY=$(aws sts get-caller-identity --profile temp_profile)

# Extract account ID from identity response
ACCOUNT_ID=$(echo "$IDENTITY" | jq -r '.Account')

# Create new profile name using account ID
NEW_PROFILE="account_${ACCOUNT_ID}"

# Configure AWS credentials with new profile
aws configure set aws_access_key_id "$ACCESS_KEY" --profile "$NEW_PROFILE"
aws configure set aws_secret_access_key "$SECRET_KEY" --profile "$NEW_PROFILE"
aws configure set region us-east-1 --profile "$NEW_PROFILE"

# Remove temporary profile
aws configure set aws_access_key_id "" --profile temp_profile
aws configure set aws_secret_access_key "" --profile temp_profile

echo "AWS credentials configured for profile: $NEW_PROFILE"
echo "You can now use this profile with: aws --profile $NEW_PROFILE"
