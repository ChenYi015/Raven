#!/bin/bash

# Note: this script is for Creating Client to Raven !
set -e

# ============= Utils function ============
function info() {
  # shellcheck disable=SC2145
  echo -e "\033[32m$@\033[0m"
}

function warn() {
  # shellcheck disable=SC2145
  echo -e "\033[33m$@\033[0m"
}

function error() {
  # shellcheck disable=SC2145
  echo -e "\033[31m$@\033[0m"
}

function logging() {
  case $1 in
  "info")
    shift
    # shellcheck disable=SC2068
    info $@
    ;;
  "warn")
    shift
    # shellcheck disable=SC2068
    warn $@
    ;;
  "error")
    shift
    # shellcheck disable=SC2068
    error $@
    ;;
  *)
    # shellcheck disable=SC2068
    echo -e $@
    ;;
  esac
}

set +e

# =============== Env Parameters =================
# Prepare Steps
## Parameter
HOME_DIR=/home/ec2-user
DEP_DIR=${HOME_DIR}/Raven/dependencies
RAVEN_HOME=/home/ec2-user/Raven
PY_DIR=/home/ec2-user/.pyenv
WHL_DIR=$DEP_DIR/wheelhouse
PYTHON_PACKAGE=Python-3.7.5.tgz

if [[ ! -d ${RAVEN_HOME} ]]; then
  logging info "Create Raven Home in ${RAVEN_HOME} ..."
  mkdir -p ${RAVEN_HOME}
fi

if [[ ! -d ${PY_DIR} ]]; then
  logging info "Create Python Home in ${PY_DIR}"
  mkdir -p ${PY_DIR}
fi

function prepare_py_env() {
  if [[ -f ${PY_DIR}/bin/python3 ]]; then
    logging warn "${PY_DIR} already exists, skip this step ..."
    return
  fi
  logging info "Decompressing ${PYTHON_PACKAGE} to ${PY_DIR} ..."
  tar -zxf ${DEP_DIR}/${PYTHON_PACKAGE} -C ${PY_DIR} --strip-components 1
}

function install_venv() {
  if [[ ! -d ${RAVEN_HOME}/.venv ]]; then
    logging info "Init Venv for Raven ..."
    ${PY_DIR}/bin/python3 -m venv ${RAVEN_HOME}/.venv
    source ${RAVEN_HOME}/.venv/bin/activate
    pip3 install --force-reinstall --ignore-installed --upgrade --no-index --no-deps ${WHL_DIR}/*
  else
    logging warn "${RAVEN_HOME}/.venv already exist, skip this step ..."
  fi
}

function main() {
  prepare_py_env
  install_venv
}

main
