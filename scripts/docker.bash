#!/bin/bash

set -e

BUILD=0
ROOT=0 
IMAGE="pfe"
WORK="$PWD"

cd "$(dirname "$0")"/..

image_exists() {
    docker images | awk -v image="$IMAGE" \
        '$1 == image {found=1} END {print found+0}'
}

if [[ $(image_exists) -eq 0 ]] || [[ $BUILD -eq 1 ]]; then
    docker build -f Dockerfile --build-arg UID=$(id -u) --build-arg GID=$(id -g) -t pfe .
fi 

RUN_CMD=(docker run -it --rm --network host --privileged)

# Enable X11 forwarding
RUN_CMD+=(
    --env="DISPLAY"
    --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw"
)

if [ $ROOT -eq 0 ]; then
    RUN_CMD+=(-u $(id -u):$(id -g))
fi

if [ "$WORK" == "$PWD" ]; then
    RUN_CMD+=(-v "$PWD:/PFE" -w /PFE)
else
    RUN_CMD+=(-v "$PWD:/PFE" -v "$WORK:/work" -w /work)
fi

RUN_CMD+=("$IMAGE")

# Execute docker run
"${RUN_CMD[@]}"
