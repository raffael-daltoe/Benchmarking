## Scarab

1. Navigate to the `testsScarab` directory to begin utilizing Scarab:

    ```bash
    cd testsScarab
    ```
    
2. In the `Makefile`, you have several configuration options to choose from:

    - The `param` folder contains the configuration file for the target processor.
    - The `codes` folder is used to create different C or C++ codes for simulation purposes.

    To use Scarab, you need to pass at least one argument, `PROGRAM`. There are also optional arguments available, such as:
    - `SCARAB_ARGS=--inst_limit`
    - `PINTOOL_ARGS=-hyper_fast_forward_count`
  
    For example, you can execute the following command:

    ```bash
    make PROGRAM=teste PINTOOL_ARGS=--hyper_fast_forward_count
    ```
