#!/bin/bash

# Logging
function info() {
  log="$(date '+%Y-%m-%d %H:%M:%S') - INFO - $*"
  echo -e "\033[32m${log}\033[0m"
}

function warning() {
  log="$(date '+%Y-%m-%d %H:%M:%S') - WARNING - $*"
  echo -e "\033[33m${log}\033[0m"
}

function error() {
  log="$(date '+%Y-%m-%d %H:%M:%S') - ERROR - $*"
  echo -e "\033[31m${log}\033[0m"
}

function logging() {
  level=$1
  shift
  case $level in
  "info")
    info "$*"
    ;;
  "warning")
    warning "$*"
    ;;
  "error")
    error "$*"
    ;;
  *)
    echo "$*"
    ;;
  esac
}

# Check prerequisites
if [ -z "${HADOOP_HOME}" ]; then
  logging error "Hadoop is not installed, please install hadoop first."
  exit 1
fi

if [ -z "${HIVE_HOME}" ]; then
  logging error "Hive is not installed, please install hive first."
  exit 1
fi

# Parse options
function usage() {
  echo "Usage: $(basename "$0"): --user <user> [--kylin-version <kylin-version>] [--kylin-mode <kylin-mode>] --mysql-host <mysql-host> \
  --mysql-username <mysql-username> --mysql-password <mysql-password> [--zookeeper-host <zookeeper-host>] --s3-path <s3-path>  [-h|--help]"
}

if ! TEMP=$(getopt -o h --long user:,spark-version:,spark-master:,s3-path:,help -- "$@"); then
  usage
fi

eval set -- "$TEMP"

while true; do
  case "$1" in
  --user)
    user="$2"
    shift 2
    ;;
  --kylin-version)
    kylin_version="$2"
    shift 2
    ;;
  --kylin-mode)
    kylin_mode="$2"
    shift 2
    ;;
  --mysql-host)
    mysql_host="$2"
    shift 2
    ;;
  --mysql-username)
    mysql_username="$2"
    shift 2
    ;;
  --mysql-password)
    mysql_password="$2"
    shift 2
    ;;
  --s3-path)
    s3_path="$2"
    shift 2
    ;;
  -h | --help)
    usage
    exit
    ;;
  --)
    shift
    break
    ;;
  *)
    usage
    exit 1
    ;;
  esac
done

# Check options
if ! id "${user}" &>/dev/null; then
  logging error "Target user must be specified."
  usage
  exit 1
fi

group=$(id -g "${user}")
home=$(grep "${user}" /etc/passwd | awk -F: '{print $6}')

if [ -z "${kylin_version}" ]; then
  kylin_version=4.0.0
  logging warning "Kylin version is not specified, use ${kylin_version} as default."
fi
kylin_tarball=apache-kylin-${kylin_version}-bin-spark3.tar.gz
kylin_home=${home}/kylin/apache-kylin-${kylin_version}-bin-spark3

if [ -z "${kylin_mode}" ]; then
  logging error "Kylin mode is not specified."
  usage
  exit 1
fi

if [ -z "${mysql_host}" ]; then
  logging error "MySQL host <mysql-host> is needed to configure \${KYLIN_HOME}/conf/kylin.properties."
  usage
  exit 1
fi

if [ -z "${mysql_username}" ]; then
  logging error "MySQL host <mysql-username> is needed to configure \${KYLIN_HOME}/conf/kylin.properties."
  usage
  exit 1
fi

if [ -z "${mysql_password}" ]; then
  logging error "MySQL host <mysql-password> is needed to configure \${KYLIN_HOME}/conf/kylin.properties."
  usage
  exit 1
fi

if [ -z "${s3_path}" ]; then
  logging error "AWS S3 path must be specified in order to download correlative tarballs, jars and other resources from s3."
  usage
  exit 1
fi

# shellcheck disable=SC2020
LOCAL_IP=$(ifconfig -a | grep inet | grep -v 127.0.0.1 | grep -v inet6 | awk '{print $2}' | tr -d "addr:")

logging info "Installing kylin4.0.0..."
mkdir -p "${home}"/kylin && cd "${home}"/kylin || exit

if [ -f ${kylin_tarball} ]; then
  logging info "${kylin_tarball} has already been downloaded."
else
  logging info "Downloading ${kylin_tarball} from ${s3_path}/tars/${kylin_tarball}..."
  aws s3 cp "${s3_path}"/tars/${kylin_tarball} .
  if [ ! -f ${kylin_tarball} ]; then
    logging error "Failed to download ${kylin_tarball}."
    exit 1
  fi
fi

if [ -d "${kylin_home}" ]; then
  logging info "${kylin_tarball} has already been decompressed."
else
  logging info "Decompressing ${kylin_tarball}..."
  if ! tar -zxf ${kylin_tarball}; then
    logging error "Failed to decompress ${kylin_tarball}."
    exit 1
  fi
fi

logging info "Copying needed jars to kylin..."
mkdir -p "${kylin_home}"/ext

if [ ! -f "${kylin_home}"/ext/mysql-connector-java-5.1.40.jar ]; then
  aws s3 cp "${s3_path}"/jars/mysql-connector-java-5.1.40.jar "${kylin_home}"/ext/
fi

if [ ! -f "${kylin_home}"/ext/slf4j-log4j12-1.7.25.jar ]; then
  cp "${HADOOP_HOME}"/share/hadoop/common/lib/slf4j-log4j12-1.7.25.jar "${kylin_home}"/ext/
fi

if [ ! -f "${kylin_home}"/ext/log4j-1.2.17.jar ]; then
  cp "${HADOOP_HOME}"/share/hadoop/common/lib/log4j-1.2.17.jar "${kylin_home}"/ext/
fi

if [ -n "$(sed -n -e '/kylin_home/p' "${home}"/.bash_profile)" ]; then
  logging info "Kylin environment variables have already been set."
else
  logging info "Setting up environment variables for kylin..."
  cat <<EOF >>"${home}"/.bash_profile

# Kylin
export kylin_home=${kylin_home}
EOF
fi
source "${home}"/.bash_profile

logging info "Modifying kylin configurations..."
if [ "${kylin_mode}" == "all" ]; then
  # shellcheck disable=SC2153
  cat <<EOF >"${KYLIN_HOME}"/conf/kylin.properties
kylin.server.mode=${kylin_mode}
kylin.metadata.url=kylin_metadata@jdbc,url=jdbc:mysql://${mysql_host}:3306/kylin,username=${mysql_username},password=${mysql_password},maxActive=10,maxIdle=10
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
elif [ "${kylin_mode}" == "query" ]; then
  cat <<EOF >"${KYLIN_HOME}"/conf/kylin.properties
kylin.server.mode=${kylin_mode}
kylin.metadata.url=kylin_metadata@jdbc,url=jdbc:mysql://${mysql_host}:3306/kylin,username=${mysql_username},password=${mysql_password},maxActive=10,maxIdle=10
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
elif [ "${kylin_mode}" == "job" ]; then
  cat <<EOF >"${KYLIN_HOME}"/conf/kylin.properties
kylin.server.mode=${kylin_mode}
kylin.metadata.url=kylin_metadata@jdbc,url=jdbc:mysql://${mysql_host}:3306/kylin,username=${mysql_username},password=${mysql_password},maxActive=10,maxIdle=10
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

logging info "Sample for kylin..."
if "${KYLIN_HOME}"/bin/sample.sh; then
  logging info "Successfully sampled for kylin."
else
  logging error "Failed to sample for kylin."
fi

logging info "Start kylin..."
if "${KYLIN_HOME}"/bin/kylin.sh run; then
  sleep 30
  logging info "Successfully started kylin."
else
  logging error "Failed to start kylin."
  exit 1
fi

KYLIN_WEB_LIB_PATH=${KYLIN_HOME}/tomcat/webapps/kylin/WEB-INF/lib
if [ ! -f "${KYLIN_WEB_LIB_PATH}"/commons-collections-3.2.2.jar ]; then
  cp "${HIVE_HOME}"/lib/commons-collections-3.2.2.jar "${KYLIN_WEB_LIB_PATH}"/
fi
if [ ! -f "${KYLIN_WEB_LIB_PATH}"/commons-configuration-1.3.jar ]; then
  aws s3 cp "${s3_path}"/jars/commons-configuration-1.3.jar "${KYLIN_WEB_LIB_PATH}"/
fi
if [ ! -f "${KYLIN_WEB_LIB_PATH}"/aws-java-sdk-bundle-1.11.375.jar ]; then
  cp "${HADOOP_HOME}"/share/hadoop/common/lib/aws-java-sdk-bundle-1.11.375.jar "${KYLIN_WEB_LIB_PATH}"/
fi
if [ ! -f "${KYLIN_WEB_LIB_PATH}"/hadoop-aws-3.2.0.jar ]; then
  cp "${HADOOP_HOME}"/share/hadoop/common/lib/hadoop-aws-3.2.0.jar "${KYLIN_WEB_LIB_PATH}"/
fi

logging info "Stoping kylin..."
"${KYLIN_HOME}"/bin/kylin.sh stop

chown -R "${user}":"${group}" "${home}"/kylin
