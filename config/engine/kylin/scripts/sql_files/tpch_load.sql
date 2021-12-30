-- Note: the path of tpch 100 is ready by user
create database if not exists ${DB};
use ${DB};

create table if not exists lineitem
(
    L_ORDERKEY      BIGINT,
    L_PARTKEY       BIGINT,
    L_SUPPKEY       BIGINT,
    L_LINENUMBER    INT,
    L_QUANTITY      DOUBLE,
    L_EXTENDEDPRICE DOUBLE,
    L_DISCOUNT      DOUBLE,
    L_TAX           DOUBLE,
    L_RETURNFLAG    STRING,
    L_LINESTATUS    STRING,
    L_SHIPDATE      STRING,
    L_COMMITDATE    STRING,
    L_RECEIPTDATE   STRING,
    L_SHIPINSTRUCT  STRING,
    L_SHIPMODE      STRING,
    L_COMMENT       STRING
)
    ROW FORMAT SERDE
        'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcSerde'
    STORED AS INPUTFORMAT
        'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcInputFormat'
        OUTPUTFORMAT
            'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcOutputFormat'
    LOCATION
        '${LOCATION}/lineitem';

create table if not exists part
(
    P_PARTKEY     BIGINT,
    P_NAME        STRING,
    P_MFGR        STRING,
    P_BRAND       STRING,
    P_TYPE        STRING,
    P_SIZE        INT,
    P_CONTAINER   STRING,
    P_RETAILPRICE DOUBLE,
    P_COMMENT     STRING
)
    ROW FORMAT SERDE
        'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcSerde'
    STORED AS INPUTFORMAT
        'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcInputFormat'
        OUTPUTFORMAT
            'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcOutputFormat'
    LOCATION
        '${LOCATION}/part';

create table if not exists supplier
(
    S_SUPPKEY   BIGINT,
    S_NAME      STRING,
    S_ADDRESS   STRING,
    S_NATIONKEY INT,
    S_PHONE     STRING,
    S_ACCTBAL   DOUBLE,
    S_COMMENT   STRING
)
    ROW FORMAT SERDE
        'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcSerde'
    STORED AS INPUTFORMAT
        'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcInputFormat'
        OUTPUTFORMAT
            'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcOutputFormat'
    LOCATION
        '${LOCATION}/supplier';

create table if not exists partsupp
(
    PS_PARTKEY    BIGINT,
    PS_SUPPKEY    BIGINT,
    PS_AVAILQTY   INT,
    PS_SUPPLYCOST DOUBLE,
    PS_COMMENT    STRING
)
    ROW FORMAT SERDE
        'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcSerde'
    STORED AS INPUTFORMAT
        'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcInputFormat'
        OUTPUTFORMAT
            'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcOutputFormat'
    LOCATION
        '${LOCATION}/partsupp';

create table if not exists nation
(
    N_NATIONKEY INT,
    N_NAME      STRING,
    N_REGIONKEY INT,
    N_COMMENT   STRING
)
    ROW FORMAT SERDE
        'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcSerde'
    STORED AS INPUTFORMAT
        'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcInputFormat'
        OUTPUTFORMAT
            'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcOutputFormat'
    LOCATION
        '${LOCATION}/nation';

create table if not exists region
(
    R_REGIONKEY INT,
    R_NAME      STRING,
    R_COMMENT   STRING
)
    ROW FORMAT SERDE
        'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcSerde'
    STORED AS INPUTFORMAT
        'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcInputFormat'
        OUTPUTFORMAT
            'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcOutputFormat'
    LOCATION
        '${LOCATION}/region';

create table if not exists customer
(
    C_CUSTKEY    BIGINT,
    C_NAME       STRING,
    C_ADDRESS    STRING,
    C_NATIONKEY  INT,
    C_PHONE      STRING,
    C_ACCTBAL    DOUBLE,
    C_MKTSEGMENT STRING,
    C_COMMENT    STRING
)
    ROW FORMAT SERDE
        'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcSerde'
    STORED AS INPUTFORMAT
        'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcInputFormat'
        OUTPUTFORMAT
            'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcOutputFormat'
    LOCATION
        '${LOCATION}/customer';

create table if not exists orders
(
    O_ORDERKEY      BIGINT,
    O_CUSTKEY       BIGINT,
    O_ORDERSTATUS   STRING,
    O_TOTALPRICE    DOUBLE,
    O_ORDERDATE     STRING,
    O_ORDERPRIORITY STRING,
    O_CLERK         STRING,
    O_SHIPPRIORITY  INT,
    O_COMMENT       STRING
)
    ROW FORMAT SERDE
        'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcSerde'
    STORED AS INPUTFORMAT
        'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcInputFormat'
        OUTPUTFORMAT
            'org.apache.hadoop-2.10.1.hive.ql.io.orc.OrcOutputFormat'
    LOCATION
        '${LOCATION}/orders';
