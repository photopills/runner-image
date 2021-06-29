# runner-image

A lightweight Docker image that extends docker/compose:alpine with our deps

## Build

```sh
docker build -f Dockerfile -t photopills/runner:latest .
docker push photopills/runner:latest
```
