#!/bin/bash
# list_ec2_instances_detailed.sh

REGION=$1

# Check if region is provided
if [ -z "$REGION" ]; then
  echo "Error: Please provide a region (e.g., us-east-1)"
  exit 1
fi

echo "Listing detailed EC2 instance information in $REGION..."
aws ec2 describe-instances \
  --profile account_903894642427 \
  --region "$REGION" \
  --query 'Reservations[].Instances[].{
    InstanceId: InstanceId,
    State: State.Name,
    InstanceType: InstanceType,
    PublicIp: PublicIpAddress,
    PrivateIp: PrivateIpAddress,
    LaunchTime: LaunchTime,
    AvailabilityZone: Placement.AvailabilityZone,
    VpcId: VpcId,
    SubnetId: SubnetId,
    KeyName: KeyName,
    Architecture: Architecture,
    RootDeviceType: RootDeviceType,
    EbsOptimized: EbsOptimized,
    Tags: Tags,
    SecurityGroups: SecurityGroups[].{GroupId: GroupId, GroupName: GroupName},
    BlockDevices: BlockDeviceMappings[].{DeviceName: DeviceName, VolumeId: Ebs.VolumeId, AttachTime: Ebs.AttachTime, DeleteOnTermination: Ebs.DeleteOnTermination},
    Monitoring: Monitoring.State,
    IamProfile: IamInstanceProfile.Arn,
    MetadataOptions: MetadataOptions.{HttpTokens: HttpTokens, HttpEndpoint: HttpEndpoint}
  }' \
  --output table 2>/dev/null || {
    echo "No EC2 instances found or access denied in $REGION"
    exit 1
  }

echo "Query completed."
