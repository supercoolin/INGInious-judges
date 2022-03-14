# DOCKER-VERSION 1.1.0

#inherit from the java container
ARG   VERSION=latest
FROM  ingi/inginious-c-java8:${VERSION}
LABEL org.inginious.grading.name="java8judge"

ADD ./javaCommon /course/
