#!/bin/bash

# Logging
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
        info "$*";;
    "warning")
        warning "$*";;
    "error")
        error "$*";;
    *)
        echo "$*";;
    esac
}

# Version
HADOOP_VERSION=2.10.1
HIVE_VERSION=2.3.7

HADOOP_PACKAGE=hadoop-${HADOOP_VERSION}.tar.gz
HIVE_PACKAGE=apache-hive-${HIVE_VERSION}-bin.tar.gz
JDK_PACKAGE=jdk-8u301-linux-x64.tar.gz
JDK_DECOMPRESS_NAME=jdk1.8.0_301


logging info "Deploying Hadoop $HADOOP_VERSION..."

if id hadoop &> /dev/null; then
    logging info "User hadoop already exists."
else
    logging info "Creating and changing user to hadoop..."
    groupadd hadoop
    useradd hadoop --gid hadoop --home-dir /home/hadoop --create-home
    "hadoop:hadoop" | sudo chpasswd
    su --login hadoop
fi

logging info "Setting up environment...."
function setup_env() {
    JAVA_HOME=/usr/local/java
    JRE_HOME=${JAVA_HOME}/jre
    HADOOP_HOME=${HOME}/hadoop-${HADOOP_VERSION}
    HIVE_HOME=${HOME}/hive

    cat << EOF >> ~/.bash_profile

# Java
export JAVA_HOME=${JAVA_HOME}
export JRE_HOME=${JRE_HOME}
export CLASSPATH=.:${JAVA_HOME}/lib:${JRE_HOME}/lib

# Hadoop
export HADOOP_HOME=${HADOOP_HOME}

# Hive
}

