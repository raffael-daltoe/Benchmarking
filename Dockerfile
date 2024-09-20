# Use Ubuntu as the base image
FROM ubuntu:20.04

# Set a custom bash prompt
RUN echo 'export PS1="workdir@PFE: \w\$ "' >> ~/.bashrc

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR PFE/

# Install required packages
RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    python3 \
    python3-pip \
    git \
    curl \
    zip \
    unzip \
    tar \
    pkg-config \
    gcc-7 \
    g++-7 \
    cmake \
    && update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-7 60 \
    && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-7 60 

# Manually download and install Clang 5.0
RUN wget https://releases.llvm.org/5.0.1/clang+llvm-5.0.1-x86_64-linux-gnu-ubuntu-16.04.tar.xz \
    && tar -xf clang+llvm-5.0.1-x86_64-linux-gnu-ubuntu-16.04.tar.xz \
    && mv clang+llvm-5.0.1-x86_64-linux-gnu-ubuntu-16.04 /opt/clang-5.0 \
    && ln -s /opt/clang-5.0/bin/clang /usr/bin/clang \
    && rm clang+llvm-5.0.1-x86_64-linux-gnu-ubuntu-16.04.tar.xz

# Download and install Pin 3.5
RUN wget https://software.intel.com/sites/landingpage/pintool/downloads/pin-3.5-97503-gac534ca30-gcc-linux.tar.gz \
    && tar -xf pin-3.5-97503-gac534ca30-gcc-linux.tar.gz -C /opt/ \
    && rm pin-3.5-97503-gac534ca30-gcc-linux.tar.gz

# Set environment variable for Pin
ENV PIN_ROOT /opt/pin-3.5-97503-gac534ca30-gcc-linux

# ChampSim configuration
RUN git clone https://github.com/ChampSim/ChampSim.git tools/ChampSim \
    && cd tools/ChampSim \
    && git submodule update --init \
    && ./vcpkg/bootstrap-vcpkg.sh \
    && ./vcpkg/vcpkg install \
    && ./config.sh champsim_config.json \
    && make -j32 \
    && cd ../..

## Scarab configuration
RUN git clone https://github.com/hpsresearchgroup/scarab.git tools/scarab \
    && cd tools/scarab/bin \
    && pip3 install -r requirements.txt \
    && cd ../../..

