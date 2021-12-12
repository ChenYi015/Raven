#!/bin/bash

# Note: this script is for AWS EMR and spark3
set -e

# Parameter
## Parameters for Spark and Kylin
METADADA_FILE=metadata-backup.sql

### ${SPARK_VERSION:0:1} get 2 from 2.4.7
SPARK_VERSION=3.1.1
KYLIN_VERSION=4.0.0
HADOOP_VERSION=3.2.0

# export val to env
export HOME_DIR=/home/hadoop
export KYLIN_HOME=${HOME_DIR}/apache-kylin-${KYLIN_VERSION}-bin-spark${SPARK_VERSION:0:1}
export SPARK_HOME=${HOME_DIR}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION:0:3}
export OUT_LOG=${HOME_DIR}/shell.stdout
export PATH_TO_BUCKET=s3://xiaoxiang-yu/kylin-xtt
export CURRENT_REGION=cn-northwest-1

## File name
KYLIN_PACKAGE=apache-kylin-${KYLIN_VERSION}-bin-spark${SPARK_VERSION:0:1}.tar.gz
SPARK_PACKAGE=spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION:0:3}.tgz

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
        "info") shift; info $@ ;;
        "warn") shift; warn $@ ;;
        "error") shift; error $@ ;;
        *) echo -e $@ ;;
    esac
}

set +e

exec 2>>${OUT_LOG}
set -o pipefail

# Main Functions and Steps
function download_and_unzip() {
    logging info "Downloading Kylin-${KYLIN_VERSION} ..."
    # download kylin & spark package
    cd ${HOME_DIR}
    ## download kylin
    aws s3 cp ${PATH_TO_BUCKET}/tar/${KYLIN_PACKAGE} ${HOME_DIR} --region ${CURRENT_REGION}
    logging info "Downloaded Kylin and start to unzip ..."
    ### unzip kylin tar file
    tar -zxf ${KYLIN_PACKAGE}
    logging info "Unzip Kylin  success."
    ### create dir directory for other dependency used by kylin
    mkdir -p ${KYLIN_HOME}/ext

    logging info "Downloading Spark-${SPARK_VERSION} ..."
    ## download spark
    aws s3 cp ${PATH_TO_BUCKET}/tar/${SPARK_PACKAGE} ${HOME_DIR} --region ${CURRENT_REGION}
    logging info "Downloaded Spark-${SPARK_VERSION} and Start to unzip ..."
    ### unzip spark tar file
    tar -zxf ${SPARK_PACKAGE}
    logging info "Unzip Spark-${SPARK_VERSION} success."
}

function replace_jars() {
    logging info "Replacing jars for Kylin ..."
    # Replace jars for kylin
    ## replace mariadb connector for kylin
    cp /usr/lib/hive/lib/mariadb-connector-java.jar ${KYLIN_HOME}/ext/
    ### copy specify jars
    cp /usr/lib/hadoop/lib/log4j-1.2.17.jar ${KYLIN_HOME}/ext/
    cp /usr/lib/hadoop/lib/slf4j-log4j12-1.7.25.jar ${KYLIN_HOME}/ext/

    logging info "Replaced jars for Kylin success."

    logging info "Replacing jars for Spark ..."
    # Replace jars in ${SPARK_HOME}/jars/
    rm -rf ${SPARK_HOME}/jars/hadoop-*.jar
    ## Use env hadoop jars to replace
    cp /usr/lib/spark/jars/hadoop-*.jar ${SPARK_HOME}/jars/
    ### copy specify jars
    cp /usr/lib/spark/jars/emr-spark-goodies.jar ${SPARK_HOME}/jars/
    cp /usr/lib/spark/jars/htrace-core4-4.1.0-incubating.jar ${SPARK_HOME}/jars/
    cp /usr/lib/hadoop-lzo/lib/hadoop-lzo-0.4.19.jar ${SPARK_HOME}/jars/
    cp /usr/lib/hadoop/lib/woodstox-core-5.0.3.jar ${SPARK_HOME}/jars/
    cp /usr/lib/livy/jars/stax2-api-3.1.4.jar ${SPARK_HOME}/jars/
    cp /usr/lib/spark/jars/emrfs-hadoop-assembly-2.46.0.jar ${SPARK_HOME}/jars/
    logging info "Replaced jars for Spark Success."
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

function prepare_metadata() {
    logging info "Check history metadata whether exists ..."
    aws s3 cp ${PATH_TO_BUCKET}/backup/emr/${METADADA_FILE} ${HOME_DIR} --region ${CURRENT_REGION}
    if [[ $? -ne 0 ]]; then
        logging warn "Metadata file: ${METADADA_FILE} not exists, so skip restore step ..."
        return
    fi

    logging info "Restoring metadata to mysql ..."
    # default user is root !
    mysql -h$(hostname -i) -u$admin -p${DATABASE_PASSWORD} < ${HOME_DIR}/${METADADA_FILE}
    logging info "Restored metadata to mysql ..."
}

#function prepare_hdfs_data() {
#
#
#}

function prepare_kylin_properties() {
    echo "kylin.metadata.url=kylin_default_instance@jdbc,url=jdbc:mysql://${DATABASE_HOST}:3306/${DATABASE_NAME},driverClassName=org.mariadb.jdbc.Driver,username=${DATABASE_USER},password=${DATABASE_PASSWORD}" >> ${KYLIN_HOME}/conf/kylin.properties
    echo "kylin.env.zookeeper-connect-string=${DATABASE_HOST}" >> ${KYLIN_HOME}/conf/kylin.properties
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
    bash -x ${KYLIN_HOME}/bin/kylin.sh run
    status=$?
    if [[ $status -ne 0 ]]; then
        logging error "Staring Kylin failed, please check on cluster."
        exit 1
    fi
    logging info "Started Kylin success, enjoy it."
}

function special_replace_step() {
  logging info "Need to replace env hive-site.xml properties"
  sudo sed -ie "s/\<value\>tez\<\/value\>/\<value\>mr\<\/value\>/g"  $KYLIN_HOME/hadoop_conf/hive-site.xml
  logging info "Replaced hive engine from tez to mr success."
}

function main() {
    download_and_unzip
    replace_jars
    init_mysql
    prepare_metadata
    # TODO: add prepare hdfs data
    prepare_hdfs_data
    prepare_kylin_properties
    start_kylin
    special_replace_step
}

main