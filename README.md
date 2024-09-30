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
    cd scripts
    ```
    
2.  Then, execute the python script:

    ```bash
    python3 champsim.py <number of threads>
    ```

The key advantage of this script, is the use of threads, basically, as the 
currently version of ChampSim doesn't allows the use of threads in only one 
simulation, this script create N simulations, with N the number of threads.

## Intel Pin
IntelIntel Pin is a dynamic binary instrumentation tool, which means it allows 
you to trace, analyze, and modify the behavior of a program as it runs.
The script ``setup.sh`` in scripts create a folder called traces and the another
one called codes.

1.  To utilize Intel Pin, first navigate to the `tracer` directory:
    
    ```bash
    cd tools/ChampSim/tracer/pin
    ```

2.  Now is necessary to choose which program you will use, for example ls, cat,
or even one executable in C, to trace a program C or C++, is mandatory to 
compile first and create a executable. 

The tracer has three options you can set:
```
-o
Specify the output file for your trace.
The default is default_trace.champsim

-s <number>
Specify the number of instructions to skip in the program before tracing begins.
The default value is 0.

-t <number>
The number of instructions to trace, after -s instructions have been skipped.
The default value is 1,000,000.
```
For example, you could trace 200,000 instructions of the program ls, after 
skipping the first 100,000 instructions, with this command:

    pin -t obj-intel64/champsim_tracer.so -o traces/ls_trace.champsim -s 100000 -t 200000 -- ls

Traces created with the champsim_tracer.so are approximately 64 bytes per 
instruction, but they generally compress down to less than a byte per 
instruction using xz compression.

