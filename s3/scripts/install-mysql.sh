#!/bin/bash

set -e

function info() {
  echo -e "\033[32m$*\033[0m"
}

function warning() {
  echo -e "\033[33m$*\033[0m"
}

function error() {
  echo -e "\033[31m$*\033[0m"
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

# MySQL
MYSQL_VERSION=5.7.31
MYSQL_ROOT_PASSWORD=root
MYSQL_DATABASE=hive

if [[ $(systemctl is-active docker) == "active" ]]; then
  logging info "Docker service has already started."
else
  logging error "Docker service has not been started, please start docker service first."
  exit 1
fi

if [ -n "$(sudo docker ps -q -f name=mysql-${MYSQL_VERSION})" ]; then
  logging info "MySQL-${MYSQL_VERSION} is running."
else
  sudo docker run -d \
  --name mysql-${MYSQL_VERSION} \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD} \
  -e MYSQL_DATABASE=${MYSQL_DATABASE} \
  mysql:${MYSQL_VERSION}
  if [ -z "$(sudo docker ps -q -f name=mysql-${MYSQL_VERSION})" ]; then
    logging error "Failed to start MySQL-${MYSQL_VERSION}."
    exit 1
  fi
fi
