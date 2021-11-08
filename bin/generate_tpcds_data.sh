# TPC-DS
git clone https://github.com/gregrahn/tpcds-kit.git /home/hadoop/tpcds-kit

TPCDS_HOME=/home/hadoop/tpcds-kit

cd $TPCDS_HOME/tools && make OS=LINUX

# 数据集规模(单位为 GB)
SCALE=1

# 数据集存放目录
DATA_DIR=$TPCDS_HOME/tpcds/data
if [ ! -d $DATA_DIR ]; then
    mkdir -p $DATA_DIR
fi

# 生成数据集(分隔符为分号)
$TPCDS_HOME/tools/dsdgen \
    -DIR $DATA_DIR \
    -SCALE ${SCALE} \
    -DELIMITER , \
    -DISTRIBUTIONS $TPCDS_HOME/tools/tpcds.idx

# 查询集存放目录
#QUERY_DIR=$TPCDS_HOME/tpcds_${SCALE}g/query
#if [ ! -d $QUERY_DIR ]; then
#    mkdir -p $QUERY_DIR
#fi

# 生成 sql 查询用例
# -QUALIFY Y 表示按顺序生成查询用例
#$TPCDS_HOME/tools/dsqgen \
#    -INPUT $TPCDS_HOME/query_templates/templates.lst \
#    -DIRECTORY $TPCDS_HOME/query_templates \
#    -SCALE ${SCALE} \
#    -QUALIFY Y \
#    -DIALECT netezza \
#    -OUTPUT_DIR $QUERY_DIR \
#    -DISTRIBUTIONS $TPCDS_HOME/tools/tpcds.idx
