
# Simulation with GEM5 Simulator

## Configuration

If binaries are available inside of codes/bin, you can proceed with starting the
simulations. 

The architecture's configuration can be modified by editing the scripts files 
inside the `scripts` folder.

To use the Python script for launching the Makefile:

    ```bash
    make exec-all
    ```

This command will execute all the binaries located in the `traces` folder.

gem5.py is configured to use only 8 threads, as using more can lead to unstable
behavior.

## Results

The `graphic.py` script in the `results` folder allows you to easily visualize 
metrics.

1. Run the following command to generate all the graphics inside results folder:

    ```bash
    python3 graphic.py
    ```