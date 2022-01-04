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
  echo "Usage: $(basename "$0"): --config-file  [-h|--help]"
}

if ! TEMP=$(getopt -o h --long config-file:,help -- "$@"); then
  usage
fi

eval set -- "$TEMP"

while true; do
  case "$1" in
  --user)
    config_file="$2"
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

if [ -z "${config_file}" ]; then
  logging error "CloudWatch config file must be specified."
  usage
  exit 1
fi

yum install -y amazon-cloudwatch-agent
mkdir -p /usr/share/collectd
touch /usr/share/collectd/types.db
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:"${config_file}"
