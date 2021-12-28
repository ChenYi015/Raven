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

logging info "Installing docker..."
if docker --version &>/dev/null; then
  logging info "Docker has already been installed."
else
  sudo yum install -y docker
  logging info "Successfully installed docker."
fi

logging info "Starting docker service..."
if [[ $(systemctl is-active docker) == "active" ]]; then
  logging info "Docker service has already started."
else
  sudo systemctl start docker
  if [[ $(systemctl is-active docker) != "active" ]]; then
    logging error "Docker service failed to start."
    exit 1
  fi
fi
