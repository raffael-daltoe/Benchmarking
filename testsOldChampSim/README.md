
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

The `graphic.py` script in the `results` folder allows you to generate 
visualizations for various metrics collected during simulations.
Choose between the Samples inside of sim_outputs to plot, for example:

    ```bash
    input_dir = '../sim_outputs/Sample4'
    ```
Change `Sample4` with the other Sample you have.

### Adding Metrics

1. **Single-Field Metrics**:  
   To include a metric with a single field (e.g., `BRANCH_DIRECT_JUMP`, 
   `BRANCH_INDIRECT`, etc.), simply add it to the `metrics_to_collect` list in 
   the `graphic.py` script.

2. **Multi-Field Metrics**:  
   For metrics with multiple fields (e.g., `cpu0_DTLB TRANSLATION`, 
   `cpu0_L1I TOTAL`, etc.), the Python script requires additional handling to 
   properly process and visualize the data.

### Running the Script

After adding the desired metrics to `metrics_to_collect`, you can execute the 
script with the following command:

1. Run the following command to generate all the graphics inside results folder:

    ```bash
    python3 graphic.py
    ```