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

## ChampSim

1.  To utilize ChampSim, first navigate to the `scripts` directory:
    
    ```bash
    cd scripts/setup.sh
    ```
    
2.  Then, execute the python script:

    ```bash
        python3 champsim.py <number of threads>
    ```

The key advantage of this script, is the use of threads, basically, as the 
currently version of ChampSim doesn't allows the use of threads in only one 
simulation, this script create N simulations, with N the number of threads.