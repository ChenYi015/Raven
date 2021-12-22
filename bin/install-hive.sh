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
  echo "Usage: $(basename "$0"): --user <user> --hive-version <hive-version> --mysql-host <mysql-host> --mysql-username
  <mysql-username> --mysql-password <mysql-password> --s3-path <s3-path> [--initialize-metastore] [--metastore-service]
  [--hiveserver2-service]  [-h|--help]"
}

if ! TEMP=$(getopt -o h --long user:,hive-version:,mysql-host:,mysql-username:,mysql-password:,s3-path:,initialize-metastore,metastore-service,hiveserver2-service,help -- "$@"); then
  usage
fi

eval set -- "$TEMP"

while true; do
  case "$1" in
  --user)
    user="$2"
    shift 2
    ;;
  --hive-version)
    hive_version="$2"
    shift 2
    ;;
  --mysql-host)
    mysql_host="$2"
    shift 2
    ;;
  --mysql-username)
    mysql_username="$2"
    shift 2
    ;;
  --mysql-password)
    mysql_password="$2"
    shift 2
    ;;
  --initialize-metastore)
    initialize-metastore=true
    shift 1
    ;;
  --metastore-service)
    metastore-service=true
    shift
    ;;
  --hiveserver2-service)
    hiveserver2-service=true
    shift
    ;;
  --s3-path)
    s3_path="$2"
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

# Check options
if ! id "${user}" &>/dev/null; then
  logging error "Target user must be specified."
  usage
  exit 1
fi

group=$(id -g "${user}")
home=$(grep "${user}" /etc/passwd | awk -F: '{print $6}')

if [ -z "${hive_version}" ]; then
  logging error "Hive version must be specified."
  usage
  exit 1
fi
hive_tarball=apache-hive-${hive_version}-bin.tar.gz
hive_home=${home}/hive/apache-hive-${hive_version}-bin

if [ -z "${mysql_host}" ]; then
  logging error "MySQL host <mysql-host> is needed to configure \${HIVE_HOME}/conf/hive-site.xml."
  usage
  exit 1
fi

if [ -z "${mysql_username}" ]; then
  logging error "MySQL host <mysql-username> is needed to configure \${HIVE_HOME}/conf/hive-site.xml."
  usage
  exit 1
fi

if [ -z "${mysql_password}" ]; then
  logging error "MySQL host <mysql-password> is needed to configure \${HIVE_HOME}/conf/hive-site.xml."
  usage
  exit 1
fi

mysql_connector_jar=mysql-connector-java-5.1.40.jar

if [ -z "${s3_path}" ]; then
  logging error "AWS S3 path <s3-path> must be specified in order to download ${hive_tarball} from s3."
  usage
  exit 1
fi

cd "${home}" || exit

if hive --version &> /dev/null; then
    logging warning "Hive has already been installed."
    exit
else
    logging info "Hive has not been installed."
fi

logging info "Installing hive-${hive_version}..."
mkdir -p "${home}"/hive && cd "${home}"/hive || exit
if [[ -f ${hive_tarball} ]]; then
    logging info "${hive_tarball} has already been downloaded..."
else
    logging info "Downloading ${hive_tarball} from ${s3_path}/${hive_tarball}..."
    if ! aws s3 cp "${s3_path}/${hive_tarball}" .; then
        logging error "Failed to download ${hive_tarball}."
        exit 1
    fi
fi

logging info "Decompressing ${hive_tarball}..."
if [[ -d ${hive_home} ]]; then
    logging info "${hive_tarball} has already been decompressed."
else
    if ! tar -zxf "${hive_tarball}"; then
	    logging error "Failed to decompress ${hive_tarball}"
	    exit 1
   fi
fi

if [[ -f ${mysql_connector_jar} ]]; then
    logging info "${mysql_connector_jar} has already been downloaded..."
else
    logging info "Downloading ${mysql_connector_jar} from ${s3_path}/${mysql_connector_jar}..."
    if ! aws s3 cp "${s3_path}/${mysql_connector_jar}" "${hive_home}"/lib; then
        logging error "Failed to download ${mysql_connector_jar}."
    fi
fi

logging info "Modifying hive configurations..."
cat << EOF > "${hive_home}"/conf/hive-site.xml
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
    <value>jdbc:mysql://${mysql_host}:3306/hive?createDatabaseIfNotExist=true&amp;useSSL=false</value>
    <description>JDBC connect string for a JDBC metastore</description>
  </property>
  <property>
    <name>javax.jdo.option.ConnectionUserName</name>
    <value>${mysql_username}</value>
    <description>Username to use against metastore database;default is root</description>
  </property>
  <property>
    <name>javax.jdo.option.ConnectionPassword</name>
    <value>${mysql_password}</value>
    <description>password to use against metastore database</description>
  </property>
  <property>
    <name>hive.metastore.schema.verification</name>
    <value>false</value>
  </property>
</configuration>
EOF

if [ -n "$(sed -n -e '/HIVE_HOME/p' "${home}"/.bash_profile)" ]; then
  logging info "Hive environment variables have already been set."
else
  logging info "Setting up environment variables for hive..."
  cat << EOF >> "${home}"/.bash_profile

# Hive
export HIVE_HOME=${hive_home}
export PATH=\${PATH}:\${HIVE_HOME}/bin
EOF
fi
source "${home}"/.bash_profile

if hive --version &> /dev/null; then
    logging info "Successfully installed hive."
else
    logging error "Failed to install hive."
    exit 1
fi

if [ "${initialize_metastore}" == true ]; then
  logging info "Initializing hive metastore..."
  # shellcheck disable=SC2153
  if "${HIVE_HOME}"/bin/schematool -dbType mysql -initSchema; then
      logging info "Successfully initialized hive metastore."
  else
      logging error "Failed to initialize hive metastore."
  fi
fi

if [ "${metastore-service}" == true ]; then
  logging info "Starting hive metastore service..."
  mkdir -p "${HIVE_HOME}"/logs
  nohup hive --service metastore &> "${HIVE_HOME}"/logs/metastore.log &
  sleep 30
  if netstat -nl | grep -q 9083; then
    logging info "Successfully started hive metastore service."
  else
    logging error "Failed to start hive metastore service."
  fi
fi

if [ "${hiveserver2-service}" == true ]; then
  logging info "Starting hiveserver2..."
  nohup hive --service hiveserver2 &> "${HIVE_HOME}"/logs/hiveserver2.log &
  sleep 30
  if netstat -nl | grep -q 10000; then
   logging info "Successfully started hiveserver2."
  else
    logging error "Failed to start hiveserver2."
  fi
fi

chown -R "${user}":"${group}" "${home}"/hive
