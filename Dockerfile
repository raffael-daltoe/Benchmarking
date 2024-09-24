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
    libtinfo-dev \
    gcc-11-multilib \
    g++-11-multilib \
    gdb \
    libstdc++-11-dev \
    libxext6 libxext-dev \
    autotools-dev \
    libc6 libc6-dev-i386 \
    libexpat-dev \
    libftdi1-dev \
    libglib2.0-dev \
    libgmp-dev \
    libmpc-dev \
    libmpfr-dev \
    libncurses5 libncurses5-dev \
    libpixman-1-dev \
    libstdc++6 libstdc++6-11-dbg \
    libtinfo5 \
    libusb-1.0-0-dev \
    libxft2  \
    clang \
    && update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-11 70 \
    && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-11 70 

# Download and install Pin 3.5
RUN wget https://software.intel.com/sites/landingpage/pintool/downloads/pin-3.5-97503-gac534ca30-gcc-linux.tar.gz \
    && tar -xf pin-3.5-97503-gac534ca30-gcc-linux.tar.gz \
    && rm pin-3.5-97503-gac534ca30-gcc-linux.tar.gz

# Set environment variable for Pin
ENV PIN_ROOT /opt/pin-3.5-97503-gac534ca30-gcc-linux

ENV PATH="/PFE/scripts:${PATH}"

COPY ../ /PFE

WORKDIR /PFE

# Create a user and group with the same UID and GID as the host user
RUN groupadd -g $GID -o PFE

RUN useradd -u $UID -m -g PFE -G plugdev PFE \
	&& echo 'PFE ALL = NOPASSWD: ALL' > /etc/sudoers.d/PFE \
	&& chmod 0440 /etc/sudoers.d/PFE

USER PFE

#RUN bash setup.sh

#RUN chmod 777 /PFE

# Set a custom bash prompt
#RUN echo 'export PS1="workdir@PFE: \w\$ "' >> ~/.bashrc

# Make the Python script executable
#RUN chmod +x scripts/pfe.py
RUN pip3 install -r scripts/requirements.txt

RUN git config --global --add safe.directory '*'
