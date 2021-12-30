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
  echo "Usage: $(basename "$0"): --user <user> --s3-path <s3-path>  [-h|--help]"
}

if ! TEMP=$(getopt -o h --long user:,s3-path:,help -- "$@"); then
  usage
fi

eval set -- "$TEMP"

while true; do
  case "$1" in
  --user)
    user="$2"
    shift 2
    ;;
  --s3-path)
    s3_path="$2"
    shift 2
    ;;
  -h | --help)
    shift
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
jdk_tarball=jdk-8u301-linux-x64.tar.gz
java_home=${home}/java/jdk1.8.0_301

if [ -z "${s3_path}" ]; then
  logging error "AWS S3 path must be specified in order to download correlative tarballs, jars and other resources from s3."
  usage
  exit 1
fi

cd "${home}" || exit

if java -version &>/dev/null; then
  logging warning "Java has already been installed."
  exit
else
  logging info "Java has not been installed."
fi

logging info "Installing Java SE 8..."
mkdir -p "${home}"/java && cd "${home}"/java || exit
if [ -f ${jdk_tarball} ]; then
  logging info "${jdk_tarball} has already been downloaded."
else
  logging info "Downloading ${jdk_tarball} from ${s3_path}/${jdk_tarball}..."
  aws s3 cp "${s3_path}"/tars/${jdk_tarball} .
  if [ ! -f ${jdk_tarball} ]; then
    logging error "Failed to download ${jdk_tarball}."
    exit 1
  fi
fi

if [ -d "${java_home}" ]; then
  logging info "${jdk_tarball} has already been decompressed."
else
  logging info "Decompressing ${jdk_tarball}..."
  if ! tar -zxf ${jdk_tarball}; then
    logging error "Failed to decompress ${jdk_tarball}."
    exit 1
  fi
fi

if [ -n "$(sed -n -e '/JAVA_HOME/p' "${home}"/.bash_profile)" ]; then
  logging info "Java environment variables have already been set."
else
  logging info "Setting up environment variables for java..."
  cat <<EOF >>"${home}"/.bash_profile

# Java
export JAVA_HOME=${java_home}
export JRE_HOME=\${JAVA_HOME}/jre
export CLASSPATH=.:\${JAVA_HOME}/lib:\${JRE_HOME}/lib
export PATH=\${PATH}:\${JAVA_HOME}/bin
EOF
fi
source "${home}"/.bash_profile

if java -version &>/dev/null; then
  logging info "Successfully installed java."
else
  logging error "Failed to install java."
  exit 1
fi

chown -R "${user}":"${group}" "${home}"/java
