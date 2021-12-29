cd "$RAVEN_HOME"

MASTER_INSTANCE_ID="i-062fb68a35e751e5c"

DISTRIBUTION="uniform"

for item in $(ls logs); do
  aws s3 cp logs/"$item" s3://olapstorage/Raven/ec2_"$MASTER_INSTANCE_ID"/"$DISTRIBUTION"/logs/
done
for item in $(ls reports/*.txt); do
  aws s3 cp "$item" s3://olapstorage/Raven/ec2_"$MASTER_INSTANCE_ID"/"$DISTRIBUTION"/
done
for item in $(ls out/workloads); do
  aws s3 cp out/workloads/"$item" s3://olapstorage/Raven/ec2_"$MASTER_INSTANCE_ID"/"$DISTRIBUTION"/workload/ --recursive
done

rm logs/*.log
rm reports/*.txt
rm -rf out/workloads/*

#
passes=300
for item in $(ls logs); do
  aws s3 cp logs/"$item" s3://olapstorage/Raven/ec2_"$MASTER_INSTANCE_ID"/"${passes}_pass"/logs/
done
for item in $(ls reports/*.txt); do
  aws s3 cp "$item" s3://olapstorage/Raven/ec2_"$MASTER_INSTANCE_ID"/"${passes}_pass"/
done
