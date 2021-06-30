# runner-image

A lightweight Docker image that extends docker/compose:alpine with our deps.

Source at https://github.com/photopills/runner-image
Image at https://hub.docker.com/r/photopills/runner

TAG | Description 
--- | --- 
`latest` | Alias of the `alpine` tag
`alpine` | An Alpine linux image with our needed tools (make, git, ...)
`python` | The latest Python over a Debian Slim linux with our needed tools (with Poetry, make tools, ...)

## Usage


Just pull latest or your desired tag with:


```sh
docker pull photopills/runner:latest
docker pull photopills/runner:alpine
docker pull photopills/runner:python
```
