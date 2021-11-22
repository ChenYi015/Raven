aws cloudwatch get-metric-statistics \
    --namespace AWS/EC2 \
    --metric-name CPUUtilization \
    --dimensions Name=InstanceId,Value=i-0e906d0ae1f9d033b \
    --statistics Average \
    --start-time 2021-11-16T14:23:01 \
    --end-time 2021-11-16T14:32:01 \
    --period 300
