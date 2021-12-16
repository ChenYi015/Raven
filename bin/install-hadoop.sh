#!/bin/bash

set -e

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

if hadoop version &> /dev/null; then
    logging warning "Hadoop already installed."
    exit
else
    logging info "Hadoop has not been installed."
fi

S3_HOME=/chenyi-ap-southeast-1
FS_S3_BUCKET=chenyi-ap-southeast-1
FS_S3A_ENDPOINT=s3.ap-southeast-1.amazonaws.com

HADOOP_VERSION=2.10.1
HADOOP_PACKAGE=hadoop-${HADOOP_VERSION}.tar.gz

logging info "Start installing hadoop ${HADOOP_VERSION}..."
cd

if [[ -f ${HADOOP_PACKAGE} ]]; then
    logging info "${HADOOP_PACKAGE} has already been downloaded."
else
    logging info "Downloading ${HADOOP_PACKAGE} from AWS s3:/${S3_HOME}/tars/${HADOOP_PACKAGE}..."
    if ! aws s3 cp s3:/${S3_HOME}/tars/${HADOOP_PACKAGE} "${HOME}"; then
        logging error "Failed to download ${HADOOP_PACKAGE}."
        exit 1
    fi
fi

HADOOP_HOME=/usr/local/hadoop/hadoop-${HADOOP_VERSION}
if [[ -d ${HADOOP_HOME} ]]; then
    logging info "${HADOOP_PACKAGE} has already been decompressed."
else
    logging info "Decompressing ${HADOOP_PACKAGE}..."
    mkdir -p /usr/local/hadoop
    if ! tar -zxf ${HADOOP_PACKAGE} -C /usr/local/hadoop; then
        logging error "Failed to decompress ${HADOOP_PACKAGE}."
        exit 1
    fi
fi

ln -s $HADOOP_HOME/share/hadoop/tools/lib/*aws* $HADOOP_HOME/share/hadoop/common/lib/

logging info "Modifying hadoop configurations..."
cat << EOF > ${HADOOP_HOME}/etc/hadoop/core-site.xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
	<property>
    <name>fs.default.name</name>
    <value>s3a:/${FS_S3_BUCKET}</value>
	</property>
  <property>
    <name>fs.s3a.endpoint</name>
    <value>${FS_S3A_ENDPOINT}</value>
  </property>
</configuration>
EOF

logging info "Setting up environment variables for hadoop..."
cat << EOF >> "${HOME}"/.bash_profile

# Hadoop
export HADOOP_HOME=${HADOOP_HOME}
export PATH=\${PATH}:\${HADOOP_HOME}/bin:\${HADOOP_HOME}/sbin
EOF
source "${HOME}"/.bash_profile

if hadoop version &> /dev/null; then
    logging info "Successfully installed hadoop."
else
    logging error "Failed to install hadoop."
    exit 1
fi