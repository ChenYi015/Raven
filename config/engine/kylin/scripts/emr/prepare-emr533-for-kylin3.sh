#!/bin/bash

# Note: this script is for AWS EMR kylin3
# TODO: to be compatible
set -e

# export val to env
export HOME_DIR=/home/hadoop
export KYLIN_HOME=${HOME_DIR}/apache-kylin-3.1.2-bin-hbase1x
export OUT_LOG=${HOME_DIR}/shell.stdout

# Parameter
## Parameters for Spark and Kylin
KYLIN_VERSION=3.1.2

## File name # apache-kylin-3.1.2-bin-hbase1x.tar.gz
KYLIN_PACKAGE=apache-kylin-${KYLIN_VERSION}-bin-hbase1x.tar.gz

## Parameter for DB
DATABASE_USER=admin
DATABASE_HOST=$(hostname -i)
DATABASE_NAME=kylin
DATABASE_PASSWORD=123456
CHARACTER_SET_SERVER=utf8
COLLATION_SERVER=utf8_unicode_ci

# Utils function
function info() {
  echo -e "\033[32m$@\033[0m"
}

function warn() {
  echo -e "\033[33m$@\033[0m"
}

function error() {
  echo -e "\033[31m$@\033[0m"
}

function logging() {
  case $1 in
  "info")
    shift
    info $@
    ;;
  "warn")
    shift
    warn $@
    ;;
  "error")
    shift
    error $@
    ;;
  *) echo -e $@ ;;
  esac
}

set +e

exec 2>>${OUT_LOG}
set -o pipefail

function basic_env() {
  cat <<EOF >>~/.bash_profile
export HIVE_HOME=/usr/lib/hive
export HADOOP_HOME=/usr/lib/hadoop
export HBASE_HOME=/usr/lib/hbase
export SPARK_HOME=/usr/lib/spark

export KYLIN_HOME=${HOME_DIR}/apache-kylin-3.1.2-bin-hbase1x
export HCAT_HOME=/usr/lib/hive-hcatalog
export KYLIN_CONF_HOME=$KYLIN_HOME/conf
export tomcat_root=$KYLIN_HOME/tomcat
export hive_dependency=$HIVE_HOME/conf:$HIVE_HOME/lib/:$HIVE_HOME/lib/hive-hcatalog-core.jar:$SPARK_HOME/jars/
export PATH=$KYLIN_HOME/bin:$PATH

export hive_dependency=$HIVE_HOME/conf:$HIVE_HOME/lib/*:$HIVE_HOME/lib/hive-hcatalog-core.jar:/usr/share/aws/hmclient/lib/*:$SPARK_HOME/jars/*:$HBASE_HOME/lib/*.jar:$HBASE_HOME/*.jar

EOF
  source ~/.bash_profile
}

# Main Functions and Steps
function download_and_unzip() {
  logging info "Downloading Kylin-${KYLIN_VERSION} ..."
  # download kylin & spark-3.1.1 package
  cd ${HOME_DIR}
  ## download kylin
  wget https://dist.apache.org/repos/dist/release/kylin/apache-kylin-${KYLIN_VERSION}/${KYLIN_PACKAGE}
  logging info "Downloaded Kylin and start to unzip ..."
  ### unzip kylin tar file
  tar -zxf ${KYLIN_PACKAGE}
  logging info "Unzip Kylin  success."

  ### copy config for kylin3 from env
  # TODO: copy hbase.zookeeper.quorum to $KYLIN_HOME/conf/kylin_job_conf.xml
  ### create dir directory for other dependency used by kylin
  # TODO: modify kylin.properties

}

function replace_jars() {

  logging info "Replacing jars for Kylin ..."
  mv $HIVE_HOME/lib/jackson-datatype-joda-2.4.6.jar $HIVE_HOME/lib/jackson-datatype-joda-2.4.6.jar.backup

  # Replace jars for kylin
  ## replace mariadb connector for kylin
  cp /usr/lib/hive/lib/mariadb-connector-java.jar ${KYLIN_HOME}/ext/
  ### copy specify jars
  cp /usr/lib/hadoop/lib/log4j-1.2.17.jar ${KYLIN_HOME}/ext/
  cp /usr/lib/hadoop/lib/slf4j-log4j12-1.7.25.jar ${KYLIN_HOME}/ext/
  logging info "Replaced jars for Kylin success."
}

function init_mysql() {
  logging info "Initing mysql for Kylin ..."
  # mysql was binding in emr
  sudo mysql -e "CREATE USER '${DATABASE_USER}'@'${DATABASE_HOST}' IDENTIFIED BY '${DATABASE_PASSWORD}';
    GRANT ALL PRIVILEGES ON *.* TO  '${DATABASE_USER}'@'${DATABASE_HOST}' WITH GRANT OPTION;
    FLUSH PRIVILEGES;
    create database if not exists ${DATABASE_NAME} default character set ${CHARACTER_SET_SERVER} collate ${COLLATION_SERVER};"
  logging info "Inited mysql for Kylin success."
}

function prepare_kylin_properties() {
  echo "kylin.metadata.url=kylin_default_instance@jdbc,url=jdbc:mysql://${DATABASE_HOST}:3306/${DATABASE_NAME},driverClassName=org.mariadb.jdbc.Driver,username=${DATABASE_USER},password=${DATABASE_PASSWORD}" >>${KYLIN_HOME}/conf/kylin.properties
  echo "kylin.env.zookeeper-connect-string=${DATABASE_HOST}" >>${KYLIN_HOME}/conf/kylin.properties
}

function sample_data() {
  logging info "Staring sample data for kylin ..."
  bash -x ${KYLIN_HOME}/bin/sample.sh
  if [[ $status -ne 0 ]]; then
    logging error "Sample data failed, please check on cluster."
    exit 1
  fi
  logging info "Sample data success, please do as followed."
  logging warn "Restart Kylin Server or click Web UI => System Tab => Reload Metadata to take effect."
}

function start_kylin() {
  logging info "Staring Kylin ..."
  export HBASE_CLASSPATH_PREFIX=${tomcat_root}/bin/bootstrap.jar:${tomcat_root}/bin/tomcat-juli.jar:${tomcat_root}/lib/*:$hive_dependency:$HBASE_CLASSPATH_PREFIX
  bash -x ${KYLIN_HOME}/bin/kylin.sh run
  status=$?
  if [[ $status -ne 0 ]]; then
    logging error "Staring Kylin failed, please check on cluster."
    exit 1
  fi
  logging info "Started Kylin success, enjoy it."
}

function main() {
  basic_env
  download_and_unzip
  init_mysql
  prepare_kylin_properties
  start_kylin
}

main
