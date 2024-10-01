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
    cd testsChampSim
    ```
    
2.  Then, you can choose these options in Makefile:
    
    If you want to execute only one program by time, i.e. compile, convert-pin,
    and trace in only command you can do:
    ```bash
    make SRC=example
    ```

    To compile the code C++ is not necessary to put '.cpp':
    ```bash
    make compile SRC=example
    ```
    
    This step now will convert the program in a way that ChampSim can read, it 
    works with C++ executables and commands in linux:
    ```bash
    make convert-pin SRC=example
    ```
    
    The final step call the binary of champsim and give the output of the test:
    ```bash
    make trace SRC=example
    ```
    
    Is possible to use the script in python too by the Makefile, the parameters
    to execute the python script can be changed in Makefile, the parameters are
    warmup_instructions, simulation_instructions and nproc that was configured
    before to .bashrc, to execute:
    ```bash
    make trace-all
    ``` 


The key advantage of this script, is the use of threads, basically, as the 
currently version of ChampSim doesn't allows the use of threads in only one 
simulation, this script create N simulations, with N the number of threads.


