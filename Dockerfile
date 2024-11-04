# Use Ubuntu as the base image
FROM ubuntu:20.04

ARG UID=1000
ARG GID=1000

# Set default shell during Docker image build to bash
SHELL ["/bin/bash", "-c"]

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Add Ubuntu Toolchain PPA
RUN apt-get update && apt-get install -y software-properties-common lsb-release \
    && add-apt-repository ppa:ubuntu-toolchain-r/test \
    && apt-get update

# Install required packages for building GCC from source
RUN apt-get update && apt-get install -y \
    software-properties-common \
    wget \
    build-essential \
    python3 \
    python3-pip \
    python3-sphinx \
    python3-dev \
    python-is-python3 \
    python3-pydot \
    pip \
    python3-venv \
    black \
    git \
    x11-apps \
    libgl1-mesa-glx \
    libx11-dev \
    curl \
    zip \
    unzip \
    lz4 \
    tar \
    pkg-config \
    scons \
    m4 \
    make \
    gcc-11 \
    g++-11 \
    gcc-11-multilib \
    g++-11-multilib \
    libsnappy-dev \
    libconfig++-dev \
    gdb \
    clang \
    libgmp-dev \
    libmpfr-dev \
    libmpc-dev \
    libcapstone-dev \
    flex \
    bison \
    doxygen \
    openssl \
    zlib1g \
    zlib1g-dev \
    libprotobuf-dev \
    protobuf-compiler \
    libprotoc-dev \
    libgoogle-perftools-dev \
    libboost-all-dev \
    libhdf5-serial-dev \
    libpng-dev \
    libelf-dev \
    sudo \
    && update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-11 70 \
    && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-11 70

# Add Kitware APT repository for the latest CMake
RUN apt-get update && \
    apt-get install -y wget gpg && \
    wget -O - https://apt.kitware.com/keys/kitware-archive-latest.asc | apt-key add - && \
    apt-add-repository 'deb https://apt.kitware.com/ubuntu/ focal main' && \
    apt-get update && \
    apt-get install -y cmake && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install GCC 7 from PPA and set up alternatives
RUN apt-get update && \
    apt-get install -y gcc-7 g++-7 gcc-7-multilib g++-7-multilib && \
    update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-7 50 && \
    update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-7 50

# Create a user and group with the same UID and GID as the host user
RUN groupadd -g $GID -o PFE \
    && useradd -u $UID -m -g PFE -G plugdev,sudo PFE

# Set no password for sudo for user PFE
RUN echo "PFE ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers.d/pfe && \
    chmod 0440 /etc/sudoers.d/pfe

# Change ownership of the alternatives directories to allow the user to switch GCC versions
RUN chown -R PFE:PFE /var/lib/dpkg /var/lib/apt /var/cache/apt /var/log/apt /var/cache/debconf /etc/apt /etc/alternatives

# Setup Intel Pin
RUN wget -P /opt http://software.intel.com/sites/landingpage/pintool/downloads/pin-3.15-98253-gb56e429b1-gcc-linux.tar.gz --no-check-certificate && \
    tar -xf /opt/pin-3.15-98253-gb56e429b1-gcc-linux.tar.gz -C /opt && \
    rm /opt/pin-3.15-98253-gb56e429b1-gcc-linux.tar.gz && \
    chown -R PFE:PFE /opt/pin-3.15-98253-gb56e429b1-gcc-linux

COPY . /PFE

WORKDIR /PFE/

#RUN bash scripts/setup.sh

# Switch to PFE user as the final step
USER PFE

# Set environment variable for Pin
ENV PIN_ROOT=/opt/pin-3.15-98253-gb56e429b1-gcc-linux

RUN echo "export PATH=/opt/pin-3.15-98253-gb56e429b1-gcc-linux:\$PATH" >> /home/PFE/.bashrc

# Install Python dependencies
RUN pip install -r scripts/requirements.txt

# Allow PFE to run without restrictions within the container
RUN git config --global --add safe.directory '*'

# Define the number of cores
ENV nproc=32
ENV SCARAB_ENABLE_MEMTRACE=1
