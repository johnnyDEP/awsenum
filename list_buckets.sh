#!/bin/bash

# List all S3 buckets the account can access and store them in a variable
buckets=$(aws s3 ls | awk '{print $3}')

# Check if any buckets were found
if [ -z "$buckets" ]; then
    echo "No buckets found or no access granted."
    exit 1
fi

# Loop through each bucket and list its contents
for bucket in $buckets; do
    echo "Listing contents of bucket: $bucket"
    aws s3 ls s3://$bucket --recursive --human-readable
    echo "----------------------------------------"
done
