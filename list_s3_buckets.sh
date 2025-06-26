#!/bin/bash
# list_s3_buckets.sh

REGION=$1

echo "Listing S3 Buckets (global resource, region: $REGION for metadata)..."
aws s3api list-buckets \
  --query "Buckets[].{Name:Name, CreationDate:CreationDate}" \
  --output table 2>/dev/null || echo "No S3 buckets found or access denied"

# Optional: Get bucket location (region) for each bucket
BUCKETS=$(aws s3api list-buckets --query "Buckets[].Name" --output text 2>/dev/null)
for BUCKET in $BUCKETS; do
  BUCKET_REGION=$(aws s3api get-bucket-location --bucket "$BUCKET" --query "LocationConstraint" --output text 2>/dev/null)
  echo "Bucket: $BUCKET, Region: ${BUCKET_REGION:-us-east-1 (default)}"
done
