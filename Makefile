# PATHs
DOCKER=/usr/bin/docker-compose
JAVA=/usr/bin/java

# Test DB
## Test DB server dockerfile
TESTDBSRVYML=../ohdsi-omop-initiated/docker-compose.yml
## Test DB data directory
TESTDBDATADIR=../omop-test-data/
## DB params
DBPARAMS=--host=localhost --port=8432 --user=postgres --password=yourpassword --database=ohdsi

# CQL on OMOP implementation
CQLONOMOPJAR=../cql-on-omop/target/cql-on-omop-1.0-SNAPSHOT.jar

.DELETE_ON_ERROR:

.PHONEY:
test-server-up:
	${DOCKER} -f ${TESTDBSRVYML} up &

.PHONEY:
test-server-down:
	${DOCKER} -f ${TESTDBSRVYML} down

.PHONEY:
run-cql-on-omop:
	${JAVA} -jar ${CQLONOMOPJAR} ${DBPARAMS}
