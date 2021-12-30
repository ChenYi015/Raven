#!/bin/bash

USER=${USER:-ec2-user}
GROUP=${GROUP:-ec2-user}
HOME=${HOME:-/home/${USER}}

cd ${HOME}
touch shell.log && chown -R ${USER}:${GROUP} shell.log

function info() {
    log="$(date '+%Y-%m-%d %H:%M:%S') - INFO - $*"
    echo -e "\033[32m${log}\033[0m"
    echo "${log}" >> ${HOME}/shell.log
}

function warning() {
    log="$(date '+%Y-%m-%d %H:%M:%S') - WARNING - $*"
    echo -e "\033[33m${log}\033[0m"
    echo "${log}" >> ${HOME}/shell.log
}

function error() {
    log="$(date '+%Y-%m-%d %H:%M:%S') - ERROR - $*"
    echo -e "\033[31m${log}\033[0m"
    echo "${log}" >> ${HOME}/shell.log
}

function logging() {
    level=$1
    shift
    case $level in
    "info")
        info "$*";;
    "warning")
        warning "$*";;
    "error")
        error "$*";;
    *)
        echo "$*";;
    esac
}

S3_HOME=s3://chenyi-ap-southeast-1

HADOOP_FS_S3_BUCKET=chenyi-ap-southeast-1

MYSQL_HOST=10.1.0.165
MYSQL_USER=kylin
MYSQL_PASSWORD=kylin

ZOOKEEPER_HOST=localhost

KYLIN_VERSION=4.0.0
KYLIN_MODE=all
KYLIN_PACKAGE=apache-kylin-${KYLIN_VERSION}-bin-spark3.tar.gz
KYLIN_HOME=${HOME}/kylin/apache-kylin-${KYLIN_VERSION}-bin-spark3

LOCAL_IP=$(ifconfig -a | grep inet | grep -v 127.0.0.1 | grep -v inet6 | awk '{print $2}' | tr -d "addr:")

logging info "Installing kylin4.0.0..."
mkdir -p ${HOME}/kylin && cd ${HOME}/kylin

if [ -f ${KYLIN_PACKAGE} ]; then
    logging info "${KYLIN_PACKAGE} has already been downloaded."
else
    logging info "Downloading ${KYLIN_PACKAGE} from ${S3_HOME}/tars/${KYLIN_PACKAGE}..."
    aws s3 cp ${S3_HOME}/tars/${KYLIN_PACKAGE} .
    if [ ! -f ${KYLIN_PACKAGE} ]; then
        logging error "Failed to download ${KYLIN_PACKAGE}."
        exit 1
    fi
fi

if [ -d ${KYLIN_HOME} ]; then
    logging info "${KYLIN_PACKAGE} has already been decompressed."
else
    logging info "Decompressing ${KYLIN_PACKAGE}..."
    if ! tar -zxf ${KYLIN_PACKAGE}; then
        logging error "Failed to decompress ${KYLIN_PACKAGE}."
        exit 1
    fi
fi

logging info "Copying needed jars to kylin..."
mkdir -p ${KYLIN_HOME}/ext

if [ ! -f ${KYLIN_HOME}/ext/mysql-connector-java-5.1.40.jar ]; then
    aws s3 cp ${S3_HOME}/jars/mysql-connector-java-5.1.40.jar ${KYLIN_HOME}/ext/
fi

if [ !  -f ${KYLIN_HOME}/ext/slf4j-log4j12-1.7.25.jar ]; then
    cp ${HADOOP_HOME}/share/hadoop/common/lib/slf4j-log4j12-1.7.25.jar ${KYLIN_HOME}/ext/
fi

if [ ! -f ${KYLIN_HOME}/ext/log4j-1.2.17.jar ]; then
    cp ${HADOOP_HOME}/share/hadoop/common/lib/log4j-1.2.17.jar ${KYLIN_HOME}/ext/
fi

if [ -n "$(sed -n -e '/KYLIN_HOME/p' ${HOME}/.bash_profile)" ]; then
    logging info "Kylin environment variables have already been set."
else
    logging info "Setting up environment variables for kylin..."
    cat << EOF >> ${HOME}/.bash_profile

# Kylin
export KYLIN_HOME=${KYLIN_HOME}
EOF
fi

source ${HOME}/.bash_profile

logging info "Modifying kylin configurations..."
if [ "${KYLIN_MODE}" == "all" ]; then
cat << EOF > ${KYLIN_HOME}/conf/kylin.properties
kylin.server.mode=${KYLIN_MODE}
kylin.metadata.url=kylin_metadata@jdbc,url=jdbc:mysql://${MYSQL_HOST}:3306/kylin,username=${MYSQL_USER},password=${MYSQL_PASSWORD},maxActive=10,maxIdle=10
kylin.env.zookeeper-connect-string=${ZOOKEEPER_HOST}
kylin.env.hdfs-working-dir=s3a://${HADOOP_FS_S3_BUCKET}/user/kylin
kylin.cube.cubeplanner.enabled=true

# Build Engine Resource
kylin.engine.spark-conf.spark.eventLog.dir=s3a://${HADOOP_FS_S3_BUCKET}/user/kylin/spark-history
kylin.engine.spark-conf.spark.history.fs.logDirectory=s3a://${HADOOP_FS_S3_BUCKET}/user/kylin/spark-history
kylin.engine.spark-conf.spark.master=spark://${LOCAL_IP}:7077
kylin.engine.spark-conf.spark.executor.cores=3
kylin.engine.spark-conf.spark.executor.instances=20
kylin.engine.spark-conf.spark.executor.memory=12GB
kylin.engine.spark-conf.spark.executor.memoryOverhead=1GB

# Parquet Column Index
kylin.engine.spark-conf.spark.hadoop.parquet.page.size=1048576
kylin.engine.spark-conf.spark.hadoop.parquet.page.row.count.limit=100000
kylin.engine.spark-conf.spark.hadoop.parquet.block.size=268435456
kylin.query.spark-conf.spark.hadoop.parquet.filter.columnindex.enabled=true

# Query Engine Resource
kylin.query.spark-conf.spark.master=spark://${LOCAL_IP}:7077
kylin.query.spark-conf.spark.driver.cores=1
kylin.query.spark-conf.spark.driver.memory=8GB
kylin.query.spark-conf.spark.driver.memoryOverhead=1G
kylin.query.spark-conf.spark.executor.instances=30
kylin.query.spark-conf.spark.executor.cores=2
kylin.query.spark-conf.spark.executor.memory=7G
kylin.query.spark-conf.spark.executor.memoryOverhead=1G
kylin.query.spark-conf.spark.sql.parquet.filterPushdown=false

# Disable canary
kylin.canary.sparder-context-canary-enabled=false

# Query Cache
kylin.query.cache-enabled=false
EOF
elif [ "${KYLIN_HOME}" == "query" ]; then
cat << EOF > ${KYLIN_HOME}/conf/kylin.properties
kylin.server.mode=${KYLIN_MODE}
kylin.metadata.url=kylin_metadata@jdbc,url=jdbc:mysql://${MYSQL_HOST}:3306/kylin,username=${MYSQL_USER},password=${MYSQL_PASSWORD},maxActive=10,maxIdle=10
kylin.env.zookeeper-connect-string=${ZOOKEEPER_HOST}
kylin.env.hdfs-working-dir=s3a://${HADOOP_FS_S3_BUCKET}/user/kylin

# Query Engine Resource
kylin.query.spark-conf.spark.master=spark://${LOCAL_IP}:7077
kylin.query.spark-conf.spark.driver.cores=1
kylin.query.spark-conf.spark.driver.memory=8GB
kylin.query.spark-conf.spark.driver.memoryOverhead=1G
kylin.query.spark-conf.spark.executor.instances=30
kylin.query.spark-conf.spark.executor.cores=2
kylin.query.spark-conf.spark.executor.memory=7G
kylin.query.spark-conf.spark.executor.memoryOverhead=1G
kylin.query.spark-conf.spark.sql.parquet.filterPushdown=false

# Disable canary
kylin.canary.sparder-context-canary-enabled=false

# Query Cache
kylin.query.cache-enabled=false
EOF
elif [ "${KYLIN_HOME}" == "job" ]; then
cat << EOF > ${KYLIN_HOME}/conf/kylin.properties
kylin.server.mode=${KYLIN_MODE}
kylin.metadata.url=kylin_metadata@jdbc,url=jdbc:mysql://${MYSQL_HOST}:3306/kylin,username=${MYSQL_USER},password=${MYSQL_PASSWORD},maxActive=10,maxIdle=10
kylin.env.zookeeper-connect-string=${ZOOKEEPER_HOST}
kylin.env.hdfs-working-dir=s3a://${HADOOP_FS_S3_BUCKET}/user/kylin
kylin.cube.cubeplanner.enabled=true

# Build Engine Resource
kylin.engine.spark-conf.spark.eventLog.dir=s3a://${HADOOP_FS_S3_BUCKET}/user/kylin/spark-history
kylin.engine.spark-conf.spark.history.fs.logDirectory=s3a://${HADOOP_FS_S3_BUCKET}/user/kylin/spark-history
kylin.engine.spark-conf.spark.master=spark://${LOCAL_IP}:7077
kylin.engine.spark-conf.spark.executor.cores=3
kylin.engine.spark-conf.spark.executor.instances=20
kylin.engine.spark-conf.spark.executor.memory=12GB
kylin.engine.spark-conf.spark.executor.memoryOverhead=1GB

# Parquet Column Index
kylin.engine.spark-conf.spark.hadoop.parquet.page.size=1048576
kylin.engine.spark-conf.spark.hadoop.parquet.page.row.count.limit=100000
kylin.engine.spark-conf.spark.hadoop.parquet.block.size=268435456
kylin.query.spark-conf.spark.hadoop.parquet.filter.columnindex.enabled=true
EOF
fi

# logging info "Sample for kylin..."
# if ${KYLIN_HOME}/bin/sample.sh; then
#     logging info "Successfully sampled for kylin."
# else
#     logging error "Failed to sample for kylin."
# fi

logging info "Start kylin..."
if ${KYLIN_HOME}/bin/kylin.sh run; then
    sleep 30
    logging info "Successfully started kylin."
else
    logging error "Failed to start kylin."
fi

    KYLIN_WEB_LIB_PATH=${KYLIN_HOME}/tomcat/webapps/kylin/WEB-INF/lib
    if [ ! -f ${KYLIN_WEB_LIB_PATH}/commons-collections-3.2.2.jar ]; then
        cp ${HIVE_HOME}/lib/commons-collections-3.2.2.jar ${KYLIN_WEB_LIB_PATH}/
    fi
    if [ ! -f ${KYLIN_WEB_LIB_PATH}/commons-configuration-1.3.jar ]; then
        aws s3 cp ${S3_HOME}/jars/commons-configuration-1.3.jar ${KYLIN_WEB_LIB_PATH}/
    fi
    if [ ! -f ${KYLIN_WEB_LIB_PATH}/aws-java-sdk-bundle-1.11.375.jar ]; then
        cp ${HADOOP_HOME}/share/hadoop/common/lib/aws-java-sdk-bundle-1.11.375.jar ${KYLIN_WEB_LIB_PATH}/
    fi
    if [ ! -f ${KYLIN_WEB_LIB_PATH}/hadoop-aws-3.2.0.jar ]; then
        cp ${HADOOP_HOME}/share/hadoop/common/lib/hadoop-aws-3.2.0.jar ${KYLIN_WEB_LIB_PATH}/
    fi

    logging info "Restarting kylin..."
    ${KYLIN_HOME}/bin/kylin.sh restart

chown -R ${USER}:${GROUP} ${HOME}/kylin
