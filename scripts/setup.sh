#!/bin/bash

# Exit on any error
set -e

# Delete all cloned submodules (if any)
git submodule deinit -f .

# Delete gitignored files/folders
git clean -Xdf

# Clone all submodules recursively
git submodule update --init --recursive

# Apply patches to submodules
for submodule in $(git submodule status | awk '{print $2}'); do
    patches="patches/$submodule"
    if [ -d "$patches" ]; then
        for patch in "$patches"/*; do
            patch=$(realpath $patch)
            (cd "$submodule" && git apply "$patch")
        done
    fi
done

# ChampSim Configuration
echo "###############    Starting ChampSim Configuration    ###############"
update-alternatives --set gcc /usr/bin/gcc-11 
update-alternatives --set g++ /usr/bin/g++-11
cp -r Polices/hawkeye tools/ChampSim/replacement/
cd tools/ChampSim 
./vcpkg/bootstrap-vcpkg.sh 
./vcpkg/vcpkg install 
./config.sh champsim_config.json 
make -j${nproc} -s
cd tracer/cvp_converter
g++ cvp2champsim.cc -o cvp_tracer 
cd ../../..

# Intel PIN Configuration
cd ChampSim/tracer/pin
make -j${nproc} -s
cd ../../../

# Scarab Configuration
echo "###############    Starting Scarab Configuration    ###############"
update-alternatives --set gcc /usr/bin/gcc-7 
update-alternatives --set g++ /usr/bin/g++-7 
cd scarab/src
make -j${nproc} -s
cd deps/dynamorio/
cmake . && make -j32
cd ../../../../

### GEM5 Configuration
echo "###############    Starting GEM5 Configuration    ###############"
update-alternatives --set gcc /usr/bin/gcc-11 
update-alternatives --set g++ /usr/bin/g++-11 
cd gem5 
echo | scons build/X86/gem5.opt -j${nproc}  # Skip the prompt
#build/X86/gem5.opt configs/learning_gem5/part1/simple.py
cd ../
