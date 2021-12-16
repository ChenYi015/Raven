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

if hive --version &> /dev/null; then
    logging warning "Hive has already been installed."
    exit
else
    logging info "Hive has not been installed."
fi

S3_HOME=s3://chenyi-ap-southeast-1

HIVE_VERSION=2.3.9
HIVE_PACKAGE=apache-hive-${HIVE_VERSION}-bin.tar.gz
HIVE_DECOMPRESS_NAME=apache-hive-${HIVE_VERSION}-bin

MYSQL_VERSION=5.7.31
MYSQL_CONNECTOR_PACKAGE=mysql-connector-java-5.1.40.jar
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=root

logging info "Installing hive${HIVE_VERSION}..."
cd

if [[ -f ${HIVE_PACKAGE} ]]; then
    logging info "${HIVE_PACKAGE} has already been downloaded..."
else
    logging info "Downloading ${HIVE_PACKAGE} from ${S3_HOME}/tars/${HIVE_PACKAGE}..."
    if ! aws s3 cp ${S3_HOME}/tars/${HIVE_PACKAGE} "${HOME}"; then
        logging error "Failed to download ${HIVE_PACKAGE}."
        exit 1
    fi
fi

logging info "Decompressing ${HIVE_PACKAGE}..."

HIVE_HOME=/usr/local/hive/${HIVE_DECOMPRESS_NAME}
if [[ -d ${HIVE_HOME} ]]; then
    logging info "${HIVE_PACKAGE} has already been decompressed."
else
		mkdir -p /usr/local/hive
    if ! tar -zxf ${HIVE_PACKAGE} -C /usr/local/hive; then
	    logging error "Failed to decompress ${HIVE_PACKAGE}"
	    exit 1
   fi
fi

if [[ -f ${MYSQL_CONNECTOR_PACKAGE} ]]; then
    logging info "${MYSQL_CONNECTOR_PACKAGE} has already been downloaded..."
else
    logging info "Downloading ${MYSQL_CONNECTOR_PACKAGE} from ${S3_HOME}/tars/${MYSQL_CONNECTOR_PACKAGE}..."
    if ! aws s3 cp ${S3_HOME}/jars/${MYSQL_CONNECTOR_PACKAGE} ${HIVE_HOME}/lib; then
        logging error "Failed to download ${MYSQL_CONNECTOR_PACKAGE}."
    fi
fi

logging info "Modifying hive configurations..."
cat << EOF > ${HIVE_HOME}/conf/hive-site.xml
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
  <property>
    <name>javax.jdo.option.ConnectionDriverName</name>
    <value>com.mysql.jdbc.Driver</value>
    <description>Driver class name for a JDBC metastore</description>
  </property>
  <property>
    <name>javax.jdo.option.ConnectionURL</name>
    <value>jdbc:mysql://${MYSQL_HOST}:3306/hive?createDatabaseIfNotExist=true&amp;useSSL=false</value>
    <description>JDBC connect string for a JDBC metastore</description>
  </property>
  <property>
    <name>javax.jdo.option.ConnectionUserName</name>
    <value>${MYSQL_USER}</value>
    <description>Username to use against metastore database;default is root</description>
  </property>
  <property>
    <name>javax.jdo.option.ConnectionPassword</name>
    <value>${MYSQL_PASSWORD}</value>
    <description>password to use against metastore database</description>
  </property>
  <property>
    <name>hive.metastore.schema.verification</name>
    <value>false</value>
    <description>
      Enforce metastore schema version consistency.
      True: Verify that version information stored in metastore matches with one from Hive jars.  Also disable automatic
            schema migration attempt. Users are required to manually migrate schema after Hive upgrade which ensures
            proper metastore schema migration. (Default)
      False: Warn if the version information stored in metastore doesn't match with one from in Hive jars.
    </description>
  </property>
</configuration>
EOF

logging info "Initializing hive metadata..."
if ${HIVE_HOME}/bin/schematool -dbType mysql -initSchema; then
    logging info "Successfully initialized hive metastore."
else
    logging error "Failed to initialize hive metastore."
    exit 1
fi

logginn info "Setting up environment variables for hive..."
cat << EOF >> "${HOME}"/.bash_profile

# Hive
export HIVE_HOME=${HIVE_HOME}
export PATH=\${PATH}:${HIVE_HOME}/bin
EOF
source "${HOME}"/.bash_profile

if hive --version &> /dev/null; then
    logging info "Successfully installed hive."
else
    logging error "Failed to install hive."
    exit 1
fi