#!/bin/bash

# Exit on error, unset variable usage, or any failed pipeline
set -euo pipefail

# Define versions of GCC
GCC_VERSION_11="/usr/bin/gcc-11"
GCC_VERSION_7="/usr/bin/gcc-7"
GPP_VERSION_11="/usr/bin/g++-11"
GPP_VERSION_7="/usr/bin/g++-7"

# Function to switch GCC versions
switch_gcc_version() {
    local gcc_version="$1"
    local gpp_version="$2"
    echo "Switching to GCC: $gcc_version and G++: $gpp_version"
    update-alternatives --set gcc "$gcc_version"
    update-alternatives --set g++ "$gpp_version"
}

# Function to apply patches to a submodule
apply_patches() {
    local submodule="$1"
    local patches_dir="patches/$submodule"
    if [ -d "$patches_dir" ]; then
        for patch in "$patches_dir"/*; do
            patch=$(realpath "$patch")
            echo "Applying patch $patch to $submodule"
            (cd "$submodule" && git apply "$patch")
        done
    fi
}

# Function to clean up git submodules
clean_submodules() {
    echo "Cleaning up all git submodules..."
    git submodule deinit -f .
    git clean -Xdf
}

# Function to initialize and update submodules
init_submodules() {
    echo "Initializing and updating git submodules..."
    git submodule update --init --recursive
}

# Function to configure and build ChampSim
configure_champsim() {
    echo "###############    Starting ChampSim Configuration    ###############"
    switch_gcc_version "$GCC_VERSION_11" "$GPP_VERSION_11"
    cp -r Policies/lib_hawkeye tools/ChampSim
    cp -r Policies/hawkeye tools/ChampSim/replacement
    cp -r Policies/bip tools/ChampSim/replacement
    cp -r Policies/emissary tools/ChampSim/replacement
    cp -r Policies/fifo tools/ChampSim/replacement
    cp -r Policies/lfu tools/ChampSim/replacement
    cp -r Policies/mockingjay tools/ChampSim/replacement
    cp -r Policies/pcn tools/ChampSim/replacement
    cp -r Policies/rlr tools/ChampSim/replacement
    cp -r Policies/random tools/ChampSim/replacement

    cp -r Branch/tage tools/ChampSim/branch
    
    cd tools/ChampSim
    ./vcpkg/bootstrap-vcpkg.sh
    ./vcpkg/vcpkg install
    ./config.sh champsim_config.json
    make -j"${nproc}" -s
    cd tracer/cvp_converter
    g++ cvp2champsim.cc -o cvp_tracer
    cd ../../..
}

# Function to configure and build Intel PIN
configure_intel_pin() {
    echo "###############    Starting Intel PIN Configuration   ###############"
    cp ../ChampSimTracer/champsim_tracer.cpp ChampSim/tracer/pin
    cd ChampSim/tracer/pin
    make -j"${nproc}" -s
    cd ../../../
}

# Function to configure and build Scarab
configure_scarab() {
    echo "###############    Starting Scarab Configuration    ###############"
    switch_gcc_version "$GCC_VERSION_7" "$GPP_VERSION_7"
    cd scarab/src
    make -j"${nproc}" -s
    cd deps/dynamorio/
    cmake . && make -j"${nproc}"
    cd ../../../../
}

# Function to configure and build GEM5
configure_gem5() {
    echo "###############    Starting GEM5 Configuration    ###############"
    switch_gcc_version "$GCC_VERSION_11" "$GPP_VERSION_11"

    cp -r ../Branch/gshare-gem5/* gem5/src/cpu/pred/ 

    #sudo cp ../Fixldgem5/ld-linux.so.3 /lib/

    cd gem5
    echo | scons build/X86/gem5.opt -j"${nproc}"  # Skip the prompt
    cd ../..
}

# Main script execution
main() {
    clean_submodules
    init_submodules

    ## Apply patches to all submodules
    for submodule in $(git submodule status | awk '{print $2}'); do
        apply_patches "$submodule"
    done

    # Execute configurations
    configure_champsim
    configure_intel_pin
    configure_scarab
    configure_gem5
}

# Run the main function
main
