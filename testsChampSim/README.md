
# Simulation with Championship Simulator

## Configuration

To run simulations, you will need trace files. The `champsim.py` script provides
an option to download traces automatically during the simulation. You just need 
to add the download links to the `trace_urls` list in the script. For example:

```python
trace_urls = [
    "https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/400.perlbench-41B.champsimtrace.xz",
    "https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/400.perlbench-50B.champsimtrace.xz"
]
```

Alternatively, you can convert programs into trace files by following these
steps:

1. Create a `.c` or `.cpp` file and place it in the `codes` folder.

2. Use the Makefile to convert the program into a trace file:

    ```bash
    make convert-pin SRC=<program>
    ```

To modify the architecture's configuration, edit the `champsim_config.json` file
located in the `param` folder.

Once everything is set up, you can start the simulations. If necessary, the 
script will automatically download the required traces.

### Running Simulations

There are two options for running simulations:

1. **Single Trace Simulation**: To run one simulation at a time, use the 
following command:

    ```bash
    make trace SRC=<program>
    ```

2. **Multiple Simulations (Multithreaded)**: To run multiple simulations 
concurrently using the `champsim.py` script, it will process all traces in the 
`traces` folder:

    ```bash
    make trace-all
    ```

You can also configure the number of simulation instructions and warm-up 
instructions (to pre-populate memory).

## Results

Results incoming...