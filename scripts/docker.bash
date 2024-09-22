#!/bin/bash

set -e

BUILD=0
ROOT=1  # Set ROOT to 1 to force root user execution
IMAGE="pfe"
WORK="$PWD"

cd "$(dirname "$0")"/..

image_exists() {
    docker images | awk -v image="$IMAGE" \
        '$1 == image {found=1} END {print found+0}'
}

if [[ $(image_exists) -eq 0 ]] || [[ $BUILD -eq 1 ]]; then
    docker build -t $IMAGE .
fi 

RUN_CMD=(docker run -it --rm --network host --user root)  # Force root user here

if [ $ROOT -eq 0 ]; then
    RUN_CMD+=(-u $(id -u):$(id -g))
    # Mount /etc/passwd and /etc/group to allow user and group name resolution
    RUN_CMD+=(-v /etc/passwd:/etc/passwd:ro -v /etc/group:/etc/group:ro)
fi

if [ "$WORK" == "$PWD" ]; then
    RUN_CMD+=(-v "$PWD:/PFE" -w /PFE)
else
    RUN_CMD+=(-v "$PWD:/PFE" -v "$WORK:/work" -w /work)
fi

RUN_CMD+=("$IMAGE")

# Execute docker run
"${RUN_CMD[@]}"
