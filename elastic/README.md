# Photopills custom ElasticSearch image

This image is built to serve our observability stack and is only used (currently) by Jaeger. The ElasticSearch (ES) version must match with the version supported by Jaeger. When upgrading the ES, to ensure that is compatible with Jaeger, please look at which [Jaeger version](https://github.com/photopills/helm/blob/master/tools/jaeger/values.yaml) we are using to select the proper ES image tag.

Our custom image currently only install the ES S3 storage plugin and configure it to use our S3 storage unit.

To build and deploy the ES image, use the following code:

1. Prepare the environment

   ```sh
   export DOCKER_BUILDKIT=1
   export DOCKER_REPO_RUNNER=cr.stack.photopills.net/runner
   # ES version supported by Jaeger
   export ELASTICSEARCH_VERSION=7.15.0
   # Our internal image tag. When upgrading, update elastic helm chart as well **
   export TAG=es-7.15.0
   ```

2. Build docker image

   ```sh
   docker build \
       --build-arg BUILDKIT_INLINE_CACHE=1 \
       --build-arg ELASTICSEARCH_VERSION=${ELASTICSEARCH_VERSION} \
       --build-arg GITHUB_TOKEN=${GITHUB_TOKEN} \
       -t ${DOCKER_REPO_RUNNER}:${TAG} \
       .

   ```

3. Deploy image to our docker registry

   `sh docker push ${DOCKER_REPO_RUNNER}:${TAG} `
