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
  echo "Usage: $(basename "$0"): --user <user> [--spark-version <spark-version>] --s3-path <s3-path>  [-h|--help]"
}

if ! TEMP=$(getopt -o h --long user:,spark-version:,s3-path:,help -- "$@"); then
  usage
fi

eval set -- "$TEMP"

while true; do
  case "$1" in
  --user)
    user="$2"
    shift 2
    ;;
  --spark-version)
    spark_version="$2"
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

if [ -z "${spark_version}" ]; then
  spark_version=3.1.1
  logging warning "Spark version is not specified, use ${spark_version} as default."
fi
spark_tarball=spark-${spark_version}-bin-hadoop3.2.tgz
spark_home=${home}/spark/spark-${spark_version}-bin-hadoop3.2

if [ -z "${s3_path}" ]; then
  logging error "AWS S3 path must be specified in order to download correlative tarballs, jars and other resources from s3."
  usage
  exit 1
fi

# Install spark
logging info "Installing Spark-${spark_version}..."
mkdir -p "${home}"/spark && cd "${home}"/spark || exit

if [[ -f ${spark_tarball} ]]; then
  logging info "${spark_tarball} has already been downloaded."
else
  logging info "Downloading ${spark_tarball} from ${s3_path}/tars/${spark_tarball}..."
  aws s3 cp "${s3_path}"/tars/${spark_tarball} .
  if [ ! -f ${spark_tarball} ]; then
    logging error "Failed to download ${spark_tarball}."
    exit 1
  fi
fi

if [ -d "${spark_home}" ]; then
  logging info "${spark_tarball} has already been decompressed."
else
  logging info "Decompressing ${spark_tarball}..."
  if ! tar -zxf ${spark_tarball}; then
    logging error "Failed to decompress ${spark_tarball}."
    exit 1
  fi
fi

logging info "Removing conflicting jars from hive..."
rm -f "${HIVE_HOME}"/lib/spark-*
rm -f "${HIVE_HOME}"/lib/jackson-module-scala_2.11-2.6.5.jar

logging info "Coping needed jars into spark from hadoop and hive"
if [ -z "$(ls "${spark_home}"/jars/hadoop-aws-*.jar)" ]; then
  cp "${HADOOP_HOME}"/share/hadoop/tools/lib/hadoop-aws-*.jar "${spark_home}"/jars/
fi

if [ ! -f "${spark_home}"/jars/aws-java-sdk-bundle-1.11.375.jar ]; then
  cp "${HADOOP_HOME}"/share/hadoop/tools/lib/aws-java-sdk-bundle-1.11.375.jar "${spark_home}"/jars/
fi

mysql_connector_jar=mysql-connector-java-5.1.40.jar
if [ ! -f "${spark_home}"/jars/${mysql_connector_jar} ]; then
  cp "$HIVE_HOME"/lib/${mysql_connector_jar} "${spark_home}"/jars/
fi

if [ ! -f "${spark_home}"/conf/hive-site.xml ]; then
  cp "${HIVE_HOME}"/conf/hive-site.xml "${spark_home}"/conf/
fi

logging info "Setting up environment variables for spark..."
cat <<EOF >>"${home}"/.bash_profile

# Spark
export SPARK_HOME=${spark_home}
export PATH=\${PATH}:\${SPARK_HOME}/bin
EOF
source "${home}"/.bash_profile

chown -R "${user}":"${group}" "${home}"/spark
