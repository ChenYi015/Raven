# 使用 TPCDS-KIT 来生成数据集和查询集

# TPCDS-KIT 家目录
# TPCDS_HOME = $(pwd)
TPCDS_HOME=~/Downloads/tpcds-kit

# 数据集规模(单位为 GB)
SCALE=1

# 数据集存放目录
DATA_DIR=$TPCDS_HOME/tpcds_${SCALE}g/data
if [ ! -d $DATA_DIR ]; then
    mkdir -p $DATA_DIR
fi

# 查询集存放目录
QUERY_DIR=$TPCDS_HOME/tpcds_${SCALE}g/query
if [ ! -d $QUERY_DIR ]; then
    mkdir -p $QUERY_DIR
fi

# 生成数据集
$TPCDS_HOME/tools/dsdgen \
    -DIR $DATA_DIR \
    -SCALE ${SCALE} \
    -DELIMITER , \
    -DISTRIBUTIONS $TPCDS_HOME/tools/tpcds.idx

# 生成 sql 测试用例
$TPCDS_HOME/tools/dsqgen \
    -INPUT $TPCDS_HOME/query_templates/templates.lst \
    -DIRECTORY $TPCDS_HOME/query_templates \
    -SCALE ${SCALE} \
    -QUALIFY Y \
    -DIALECT oracle \
    -OUTPUT_DIR $QUERY_DIR \
    -DISTRIBUTIONS $TPCDS_HOME/tools/tpcds.idx