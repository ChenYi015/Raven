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
        info "$*";;
    "warning")
        warning "$*";;
    "error")
        error "$*";;
    *)
        echo "$*";;
    esac
}

if java -version &> /dev/null; then
    logging warning "Java has already been installed."
    exit
else
    logging info "Java has not been installed."
fi

logging info "Installing Java SE 8..."
JDK_PACKAGE=jdk-8u301-linux-x64.tar.gz
JDK_DECOMPRESS_NAME=jdk1.8.0_301
S3_HOME=/chenyi-ap-southeast-1

if [[ -f ${JDK_PACKAGE} ]]; then
    logging info "${JDK_PACKAGE} has already been downloaded."
else
    logging info "Downloading ${JDK_PACKAGE} from s3:/${S3_HOME}/tars/${JDK_PACKAGE}..."
    aws s3 cp s3:/${S3_HOME}/tars/${JDK_PACKAGE} "${HOME}"
    if [[ ! -f ${JDK_PACKAGE} ]]; then
        logging error "Failed to download ${JDK_PACKAGE}."
        exit 1
    fi
fi


JAVA_HOME=/usr/local/java/${JDK_DECOMPRESS_NAME}
JRE_HOME=${JAVA_HOME}/jre
if [[ -d ${JAVA_HOME} ]]; then
    logging info "${JDK_PACKAGE} has already been decompressed."
else
    logging info "Decompressing ${JDK_PACKAGE}..."
    mkdir -p /usr/local/java
    if ! tar -zxf ${JDK_PACKAGE} -C /usr/local/java; then
	    logging error "Failed to decompress ${JDK_PACKAGE}."
	    exit 1
    fi
fi

logging info "Setting up environment variables for java..."
cat << EOF >> "${HOME}"/.bash_profile

# Java
export JAVA_HOME=${JAVA_HOME}
export JRE_HOME=${JRE_HOME}
export CLASSPATH=.:${JAVA_HOME}/lib:${JRE_HOME}/lib
export PATH=${PATH}:${JAVA_HOME}/bin
EOF
source "${HOME}"/.bash_profile

if java -version &> /dev/null; then
    logging info "Successfully installed java."
else
    logging error "Failed to install java."
    exit 1
fi
