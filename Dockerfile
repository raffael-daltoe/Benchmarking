# Use Ubuntu as the base image
FROM ubuntu:20.04

# Set a custom bash prompt
RUN echo 'export PS1="workdir@PFE: \w\$ "' >> ~/.bashrc

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /PFE/

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
    gcc-10 \
    g++-10 \
    cmake \
    scons \
    m4 \
    && update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-7 60 \
    && update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-10 70 \
    && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-7 60 \
    && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-10 70

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

COPY . .
RUN git init && git submodule init

# GEM5 configuration with GCC 10
RUN update-alternatives --set gcc /usr/bin/gcc-10 \
    && update-alternatives --set g++ /usr/bin/g++-10 \
    && cd tools/gem5 \
    && scons build/X86/gem5.opt -j32 \
    && build/X86/gem5.opt configs/learning_gem5/part1/simple.py

# ChampSim configuration
RUN cd tools/ChampSim \
    #&& git submodule update --init \
    && ./vcpkg/bootstrap-vcpkg.sh \
    && ./vcpkg/vcpkg install \
    && ./config.sh champsim_config.json \
    && make -j32 \
    && cd ../..

# Scarab configuration
RUN update-alternatives --set gcc /usr/bin/gcc-7 \
    && update-alternatives --set g++ /usr/bin/g++-7 \
    && cd tools/scarab/bin \
    && pip3 install -r requirements.txt \
    && cd ../src \
    && make -j32 \
    && cd ../../..