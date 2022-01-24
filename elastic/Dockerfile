ARG ELASTICSEARCH_VERSION
ARG DO_ACCESS_KEY_ID
ARG DO_SECRET_ACCESS_KEY
FROM docker.elastic.co/elasticsearch/elasticsearch:${ELASTICSEARCH_VERSION}

RUN elasticsearch-plugin install --batch repository-s3

# Inject credentials
RUN echo ${DO_ACCESS_KEY_ID} | /usr/share/elasticsearch/bin/elasticsearch-keystore add --stdin s3.client.default.access_key \
    && echo ${DO_SECRET_ACCESS_KEY} | /usr/share/elasticsearch/bin/elasticsearch-keystore add --stdin s3.
