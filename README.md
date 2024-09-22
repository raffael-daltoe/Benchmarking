# Benchmark of Processors and Architectures

This repository includes a Dockerfile that manages the setup of ChampSim, 
Scarab, and Gem5. The goal is to simulate various processors and architectures 
with custom testbenches.

## Configuration

To configure the environment, follow these steps:

1. In the `Benchmarking` directory, run the following command to build the 
Docker container:

    ```bash
    ./scripts/docker.bash
    ```

2. Once the container is created, initialize the setup inside the image by 
running:

    ```bash
    ./scripts/setup.sh
    ```

This will prepare the environment for running simulations.
