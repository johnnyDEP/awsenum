#!/bin/bash
# list_elasticache_redis.sh

REGION=$1

echo "Listing ElastiCache Redis Instances in $REGION..."
aws elasticache describe-cache-clusters \
  --region "$REGION" \
  --query "CacheClusters[?Engine=='redis'].{ClusterId:CacheClusterId, Engine:Engine, Status:CacheClusterStatus, NodeType:CacheNodeType, Endpoint:Endpoint.Address}" \
  --output table 2>/dev/null || echo "No Redis instances found or access denied in $REGION"
