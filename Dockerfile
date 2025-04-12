FROM apache/airflow:2.7.0

USER root

RUN rm -f /etc/apt/sources.list.d/mysql.list

RUN apt update && \
    apt-get install -y openjdk-17-jdk ant && \
    apt-get clean;

# Set JAVA_HOME
ENV JAVA_HOME /usr/lib/jvm/java-17-openjdk-amd64/
RUN export JAVA_HOME

USER airflow

RUN pip install pyspark pandas requests