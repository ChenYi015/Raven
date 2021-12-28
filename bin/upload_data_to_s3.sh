cd "$RAVEN_HOME"

EMR_CLUSTER_ID=j-2Y4SF4KIBSQUM

DISTRIBUTION=shrink

for item in $(ls logs); do
  aws s3 cp logs/"$item" s3://olapstorage/Raven/emr_"$EMR_CLUSTER_ID"/"$DISTRIBUTION"/logs/
done
for item in $(ls reports/*.txt); do
  aws s3 cp "$item" s3://olapstorage/Raven/emr_"$EMR_CLUSTER_ID"/"$DISTRIBUTION"/
done
for item in $(ls out/workloads); do
  aws s3 cp out/workloads/"$item" s3://olapstorage/Raven/emr_"$EMR_CLUSTER_ID"/"$DISTRIBUTION"/workload/ --recursive
done

rm logs/*.log
rm reports/*.txt
rm -rf out/workloads/*

# presto-0.266.1 config.properties
sudo aws s3 cp /etc/presto/conf/config.properties s3://olapstorage/Raven/emr_"$EMR_CLUSTER_ID"/
