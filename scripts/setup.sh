#!/bin/bash

# Setup submodules
# =============================================================================
echo "Initializing and updating submodules recursively..."
git submodule update --init --recursive

# Apply patches to submodules if any
echo "Applying patches to submodules..."
for submodule in $(git submodule status | awk '{print $2}'); do
    patches="patches/$submodule"
    if [ -d "$patches" ]; then
        for patch in "$patches"/*; do
            patch=$(realpath $patch)
            (cd "$submodule" && git apply "$patch")
            git submodule update --init
        done
    fi
done


docker build -f Dockerfile -t pfe .
docker run -v $(pwd):/PFE -it pfe 