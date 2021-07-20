FROM docker/compose:alpine-1.29.2

RUN apk add make nodejs npm yarn make git openssh
