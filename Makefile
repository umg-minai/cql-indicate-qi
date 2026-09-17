CQL_ON_OMOP_JAR ?= cql-on-omop-1.1.9-SNAPSHOT.jar

.PHONY: test

test:
	@TZ=CET java -jar $(CQL_ON_OMOP_JAR) batch -I cql/ Test         \
	  -D"IndicateQiUtilities.OnError='continue'"                    \
          --result-name="Results" --print-results-matching='Results'
