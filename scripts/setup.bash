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
    cp -r Polices/hawkeye/lib_hawkeye tools/ChampSim
    cp -r Polices/hawkeye/Hawkeye_Predictor tools/ChampSim/replacement
    cp -r Polices/bip tools/ChampSim/replacement
    cp -r Polices/emissary tools/ChampSim/replacement
    cp -r Polices/fifo tools/ChampSim/replacement
    cp -r Polices/lfu tools/ChampSim/replacement
    cp -r Polices/mockingjay tools/ChampSim/replacement

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
    cd gem5
    echo | scons build/X86/gem5.opt -j"${nproc}"  # Skip the prompt
    # build/X86/gem5.opt configs/learning_gem5/part1/simple.py
    cd ..
}

# Main script execution
main() {
    clean_submodules
    init_submodules

    # Apply patches to all submodules
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
