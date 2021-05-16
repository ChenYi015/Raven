aws emr create-cluster --auto-scaling-role EMR_AutoScaling_DefaultRole --applications Name=Hadoop Name=Hive Name=Spark --ebs-root-volume-size 100 --ec2-attributes '{"KeyName":"olap","InstanceProfile":"EMR_EC2_DefaultRole","SubnetId":"subnet-1661c970","EmrManagedSlaveSecurityGroup":"sg-0489d2178d7217ed0","EmrManagedMasterSecurityGroup":"sg-01f8a75069f70f275"}' --service-role EMR_DefaultRole --release-label emr-5.29.0 --name 'olap_test' --instance-groups '[{"InstanceCount":2,"BidPrice":"OnDemandPrice","EbsConfiguration":{"EbsBlockDeviceConfigs":[{"VolumeSpecification":{"SizeInGB":100,"VolumeType":"gp2"},"VolumesPerInstance":1}],"EbsOptimized":false},"InstanceGroupType":"CORE","InstanceType":"m4.large","Name":"master"},{"InstanceCount":1,"BidPrice":"OnDemandPrice","EbsConfiguration":{"EbsBlockDeviceConfigs":[{"VolumeSpecification":{"SizeInGB":100,"VolumeType":"gp2"},"VolumesPerInstance":1}],"EbsOptimized":true},"InstanceGroupType":"MASTER","InstanceType":"m4.large","Name":"slave"}]' --scale-down-behavior TERMINATE_AT_TASK_COMPLETION --region ap-southeast-1