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

if [ -z "${SPARK_HOME}" ]; then
  logging error "Spark is not installed, please install spark first."
  exit 1
fi

# Parse options
function usage() {
  echo "Usage: $(basename "$0"): --user <user> [--zookeeper-version <zookeeper-version>] --s3-path <s3-path>  [-h|--help]"
}

if ! TEMP=$(getopt -o h --long user:,zookeeper-version:,s3-path:,help -- "$@"); then
  usage
fi

eval set -- "$TEMP"

while true; do
  case "$1" in
  --user)
    user="$2"
    shift 2
    ;;
  --zookeeper-version)
    zookeeper_version="$2"
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

if [ -z "${zookeeper_version}" ]; then
  zookeeper_version=3.4.14
  logging warning "Kylin version is not specified, use ${zookeeper_version} as default."
fi

if [ -z "${s3_path}" ]; then
  logging error "AWS S3 path must be specified in order to download correlative tarballs, jars and other resources from s3."
  usage
  exit 1
fi

zookeeper_tarball=zookeeper-${zookeeper_version}.tar.gz
zookeeper_home=${home}/zookeeper/zookeeper-${zookeeper_version}

logging info "Installing zookeeper-${zookeeper_version}..."
mkdir -p "${home}"/zookeeper && cd "${home}"/zookeeper || exit

if [ ! -f ${zookeeper_tarball} ]; then
  aws s3 cp "${s3_path}"/tars/${zookeeper_tarball} .
fi

if [ ! -d "${zookeeper_home}" ]; then
  tar -zxf ${zookeeper_tarball}
fi

if [ -z "$(sed -n -e '/ZOOKEEPER_HOME/p' "${home}"/.bash_profile)" ]; then
  logging info "Setting up zookeeper environment variables..."
  cat <<EOF >>"${home}"/.bash_profile

# Zookeeper
ZOOKEEPER_HOME=${zookeeper_home}
EOF
fi
source "${home}"/.bash_profile

logging info "Modifying zookeeper configurations..."
for i in {1..3}; do
  # shellcheck disable=SC2153
  cat <<EOF >"${ZOOKEEPER_HOME}"/conf/zoo"${i}".cfg
# zoo${i}.cfg
tickTime=2000
initLimit=10
syncLimit=5
server.1=localhost:2287:3387
server.2=localhost:2288:3388
server.3=localhost:2289:3389
dataDir=/tmp/zookeeper/zk${i}/data
dataLogDir=/tmp/zookeeper/zk${i}/log
clientPort=218${i}
EOF
  mkdir -p "/tmp/zookeeper/zk${i}/log"
  mkdir -p "/tmp/zookeeper/zk${i}/data"
  echo "${i}" >>"/tmp/zookeeper/zk${i}/data/myid"
done

chmod -R 777 /tmp/zookeeper
chown -R "${user}":"${group}" "${home}"/zookeeper
