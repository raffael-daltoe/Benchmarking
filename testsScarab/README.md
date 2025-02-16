
# Simulation with Scarab Simulator

## Configuration

To start the simulations, you need to have some traces. In this case, Dynamorio 
was used to create these traces, though Intel PIN could also be used.

1. In the root folder of `testsScarab`, first create a C or C++ program and 
place it in the `codes` folder. Then, if necessary, use the Makefile to generate 
new traces:

    ```bash
    make trace-program PROGRAM=<program>
    ```

If traces are already available, you can proceed with starting the simulations. 

The architecture's configuration can be modified by editing the `param.in` 
file inside the `param` folder.

To use the Python script for launching the Makefile:

    ```bash
    make launch PROGRAM=<program>
    ```

To run the simulation using the binary with the Makefile:

    ```bash
    make launch-trace SIM_OUT=<folder> PROGRAM=<program>
    ```

The `scarab.py` script, located in the `testsScarab` folder, enables 
multithreaded simulations, allowing multiple simulations to run in parallel.

    ```bash
    make launch-all
    ```

This command will execute all the traces located in the `traces` folder.

## Results

The `graphic.py` script in the `results` folder allows you to easily visualize 
metrics.

1. Run the following command to generate all the graphics inside results folder:

    ```bash
    python3 graphic.py
    ```