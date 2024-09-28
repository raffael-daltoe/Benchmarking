# Use Ubuntu as the base image
FROM ubuntu:20.04

ARG UID=1000
ARG GID=1000

# Set default shell during Docker image build to bash
SHELL ["/bin/bash", "-c"]

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Add Ubuntu Toolchain PPA for GCC 11
RUN apt-get update && apt-get install -y software-properties-common \
    && add-apt-repository ppa:ubuntu-toolchain-r/test \
    && apt-get update

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
    gcc-11 \
    g++-11 \
    cmake \
    scons \
    m4 \
    sudo \
    gcc-11-multilib \
    g++-11-multilib \
    gdb \
    clang \
    && update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-11 70 \
    && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-11 70 

COPY ../ /PFE

WORKDIR /PFE

# Create a user and group with the same UID and GID as the host user
RUN groupadd -g $GID -o PFE

RUN useradd -u $UID -m -g PFE -G plugdev PFE \
	&& echo 'PFE ALL = NOPASSWD: ALL' > /etc/sudoers.d/PFE \
	&& chmod 0440 /etc/sudoers.d/PFE

# Setup Intel Pin
RUN wget -P /opt https://software.intel.com/sites/landingpage/pintool/downloads/pin-3.22-98547-g7a303a835-gcc-linux.tar.gz --no-check-certificate && \
    tar -xf /opt/pin-3.22-98547-g7a303a835-gcc-linux.tar.gz -C /opt && \
    rm /opt/pin-3.22-98547-g7a303a835-gcc-linux.tar.gz && \
    chown -R PFE:PFE /opt/pin-3.22-98547-g7a303a835-gcc-linux


USER PFE

# Set environment variable for Pin
ENV PIN_ROOT /opt/pin-3.22-98547-g7a303a835-gcc-linux

# Add Pin tool to PATH for PFE user 
RUN echo "export PATH=/opt/pin-3.22-98547-g7a303a835-gcc-linux:\$PATH" >> ~/.bashrc

RUN pip3 install -r scripts/requirements.txt

RUN git config --global --add safe.directory '*'