FROM eclipse-temurin:21-jdk-alpine

RUN addgroup -S sandbox \
    && adduser -S -D -H -u 10001 -G sandbox sandbox

COPY sandbox-images/java_runner.sh /usr/local/bin/java_runner.sh
RUN chmod 0555 /usr/local/bin/java_runner.sh

USER sandbox
WORKDIR /sandbox

ENTRYPOINT ["/usr/local/bin/java_runner.sh"]
