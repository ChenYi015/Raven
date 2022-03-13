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

# Parse options
function usage() {
  echo "Usage: $(basename "$0"): --user <user> [--presto-version <presto-version>] --include-coordinator <include-coordinator> [--hive-metastore-uri <hive-metastore-uri>] --s3-path <s3-path>  [-h|--help]"
}

if ! TEMP=$(getopt -o h --long user:,presto-version:,include-coordinator,hive-metastore-uri:,s3-path:,help -- "$@"); then
  usage
fi

eval set -- "$TEMP"

while true; do
  case "$1" in
  --user)
    user="$2"
    shift 2
    ;;
  --presto-version)
    presto_version="$2"
    shift 2
    ;;
  --include-coordinator)
    include_coordinator=true
    shift
    ;;
  --hive-metastore-uri)
    hive_metastore_uri="$2"
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

if [ -z "${presto_version}" ]; then
  presto_version=0.266.1
  logging warning "Presto version is not specified, use ${presto_version} as default."
fi
presto_tarball=presto-server-${presto_version}.tar.gz
presto_client_jar=presto-cli-${presto_version}-executable.jar
presto_home=${home}/presto/presto-server-${presto_version}

if [ -z "${include_coordinator}" ]; then
  include_coordinator=false
  logging warning "Property node-scheduler.include-coordinator is not specified, use ${include_coordinator} as default to configure \${PRESTO_HOME}/etc/config.properties."
fi

if [ -z "${hive_metastore_uri}" ]; then
  hive_metastore_uri=http://$(hostname):8080
  logging warning "Property hive.metastore.uri is not specified, use ${hive_metastore_uri} as default to configure \${PRESTO_HOME}/etc/catalog/hive.properties."
fi

if [ -z "${s3_path}" ]; then
  logging error "AWS S3 path must be specified in order to download correlative tarballs, jars and other resources from s3."
  usage
  exit 1
fi

logging info "Installing Presto-${presto_version}..."
mkdir -p "${home}"/presto && cd "${home}"/presto || exit

if [ -f ${presto_tarball} ]; then
  logging warning "${presto_tarball} has already been downloaded."
else
  logging info "Downloading ${presto_tarball} from AWS ${s3_path}/tars/${presto_tarball}..."
  if ! aws s3 cp "${s3_path}"/tars/${presto_tarball} .; then
    logging error "Failed to download ${presto_tarball}"
    exit 1
  fi

if [ -d "${presto_home}" ]; then
  logging warning "${presto_tarball} has already been decompressed."
else
  logging info "Decompressing ${presto_tarball}..."
  tar -zxf ${presto_tarball}
  if [ ! -d "${presto_home}" ]; then
    logging error "Failed to decompress ${presto_tarball}."
    exit 1
  fi
fi

if [ -n "$(sed -n -e '/PRESTO_HOME/p' "${home}"/.bash_profile)" ]; then
  logging warning "Presto environment variables have already been set."
else
  logging info "Setting up environment variables for presto."
  cat <<EOF >>"${home}"/.bash_profile

# Presto
PRESTO_HOME=${presto_home}
PATH=\${PATH}:\${PRESTO_HOME}/bin
EOF
fi
source "${home}"/.bash_profile

logging info "Modifying presto configurations..."
# shellcheck disable=SC2153
mkdir -p "${PRESTO_HOME}"/etc

cat <<EOF >"${PRESTO_HOME}"/etc/config.properties
coordinator=true
node-scheduler.include-coordinator=${include_coordinator}
query.max-memory=128GB
query.max-memory-per-node=20GB
query.max-total-memory-per-node=32GB
http-server.http.port=8080
discovery-server.enabled=true
discovery.uri=http://$(hostname):8080
EOF

cat <<EOF >"${PRESTO_HOME}"/etc/jvm.config
-server
-Xmx48G
-XX:+UseG1GC
-XX:G1HeapRegionSize=32M
-XX:+UseGCOverheadLimit
-XX:+ExplicitGCInvokesConcurrent
-XX:+HeapDumpOnOutOfMemoryError
-XX:+ExitOnOutOfMemoryError
EOF

cat <<EOF >"${PRESTO_HOME}"/etc/node.properties
node.environment=production
node.id=presto-production-coordinator-with-id-1
node.data-dir=${PRESTO_HOME}/data
EOF

mkdir -p "${PRESTO_HOME}"/etc/catalog

cat <<EOF >"${PRESTO_HOME}"/etc/catalog/hive.properties
connector.name=hive-hadoop2
hive.metastore.uri=${hive_metastore_uri}
EOF

cat <<EOF >"${PRESTO_HOME}"/etc/log.properties
com.facebook.presto=INFO
EOF

logging info "Installing presto client..."
if [ ! -f "${PRESTO_HOME}"/bin/presto ]; then
  aws s3 cp "${s3_path}"/jars/${presto_client_jar} "${PRESTO_HOME}"/bin/presto
fi
if [ ! -x "${PRESTO_HOME}"/bin/presto ]; then
  chmod u+x "${PRESTO_HOME}"/bin/presto
fi
logging info "Successfully installed presto client."

chown -R "${user}":"${group}" "${home}"/presto
