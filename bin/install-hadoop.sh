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
  echo "Usage: $(basename "$0"): --user <user> --hadoop-version <hadoop-version> --fs-default-name <fs-default-name> --fs-s3a-endpoint <fs-s3a-endpoint> --s3-path <s3-path>  [-h|--help]"
}

if ! TEMP=$(getopt -o h --long hadoop-version:,user:,fs-default-name:,fs-s3a-endpoint:,s3-path:,help -- "$@"); then
  usage
fi

eval set -- "$TEMP"

while true; do
  case "$1" in
  --user)
    user="$2"
    shift 2
    ;;
  --hadoop-version)
    hadoop_version="$2"
    shift 2
    ;;
  --fs-default-name)
    fs_default_name=$2
    shift 2
    ;;
  --fs-s3a-endpoint)
    fs_s3a_endpoint="$2"
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
  logging error "Target user."
  usage
  exit 1
fi

group=$(id -g "${user}")
home=$(grep "${user}" /etc/passwd | awk -F: '{print $6}')

if [ -z "${hadoop_version}" ]; then
  logging error "Hadoop version <hadoop-version> must be specified."
  usage
  exit 1
fi

hadoop_package=hadoop-${hadoop_version}.tar.gz

if [ -z "${fs_default_name}" ]; then
  logging error "Property 'fs.default.name' is needed to configure \${HADOOP_HOME}/etc/hadoop/core-site.xml."
  usage
  exit 1
fi

if [ -z "${fs_s3a_endpoint}" ]; then
  logging error "Property 'fs.s3a.endpoint' is needed to configure \${HADOOP_HOME}/etc/hadoop/core-site.xml."
  usage
  exit 1
fi

if [ -z "${s3_path}" ]; then
  logging error "AWS S3 path must be specified in order to download correlative tarballs, jars and other resources from s3."
  usage
  exit 1
fi

cd "${home}" || exit

if hadoop version &>/dev/null; then
  logging warning "Hadoop has already been installed."
  exit
else
  logging info "Hadoop has not been installed."
fi

logging info "Start installing hadoop-${hadoop_version}..."
mkdir -p "${home}"/hadoop && cd "${home}"/hadoop || exit
if [[ -f ${hadoop_package} ]]; then
  logging info "${hadoop_package} has already been downloaded."
else
  logging info "Downloading ${hadoop_package} from AWS ${s3_path}/${hadoop_package}..."
  if ! aws s3 cp "${s3_path}"/"${hadoop_package}" .; then
    logging error "Failed to download ${hadoop_package}."
    exit 1
  fi
fi

hadoop_home=${home}/hadoop/hadoop-${hadoop_version}
if [[ -d ${hadoop_home} ]]; then
  logging info "${hadoop_package} has already been decompressed."
else
  logging info "Decompressing ${hadoop_package}..."
  if ! tar -zxf "${hadoop_package}"; then
    logging error "Failed to decompress ${hadoop_package}."
    exit 1
  fi
fi
cp "${hadoop_home}"/share/hadoop/tools/lib/*aws* "${hadoop_home}"/share/hadoop/common/lib/

logging info "Modifying hadoop configurations..."
cat <<EOF >"${hadoop_home}"/etc/hadoop/core-site.xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
	<property>
    <name>fs.default.name</name>
    <value>s3a://${fs_default_name}</value>
	</property>
  <property>
    <name>fs.s3a.endpoint</name>
    <value>${fs_s3a_endpoint}</value>
  </property>
</configuration>
EOF

logging info "Setting up environment variables for hadoop..."
cat <<EOF >>"${home}"/.bash_profile

# Hadoop
export HADOOP_HOME=${hadoop_home}
export PATH=\${PATH}:\${HADOOP_HOME}/bin:\${HADOOP_HOME}/sbin
EOF
source "${home}"/.bash_profile

if hadoop version &>/dev/null; then
  logging info "Successfully installed hadoop."
else
  logging error "Failed to install hadoop."
  exit 1
fi

chown -R "${user}":"${group}" "${home}/hadoop"
