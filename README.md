# runner-image

A lightweight Docker image that extends docker/compose:alpine with our deps

https://hub.docker.com/r/photopills/runner

## Build

```sh
docker build -f Dockerfile -t photopills/runner:latest .
docker push photopills/runner:latest
```
