# Author: Raffael Rocha Daltoe
# Polytech Montpellier - 2024

CC = gcc
CPP = g++
CFLAGS =

SCARAB_DIR = ../tools/scarab
DYNAMORIO_DIR = $(SCARAB_DIR)/src/deps/dynamorio
CODES_DIR = codes
SIMULATION_OUTPUTS = sim_outputs
PARAM_DIR = param
TRACE_DIR = traces
ATUAL_DIR = 

PARAM ?=
PROGRAM ?=

# PARAMETERS TO CHANGE FOR PYTHON SCRIPT
#####################################################

ENABLE_ASLR  ?=
SCARAB_ARGS  ?=
PINTOOL_ARGS ?=
SIMULATION_INSTRUCTIONS = 100

#####################################################

# Default target
all: compile check-param check-program launch

check-param:
ifeq ($(strip $(PARAM)),)
	@echo "Param config not defined, using the standard in $(PARAM_DIR)/"
	$(eval PARAM := $(PARAM_DIR)/param.in)
#	$(error "PARAM config is not defined. Please provide a file for PARAM.")
endif

check-program:
ifeq ($(strip $(PROGRAM)),)
	$(error "PROGRAM is not defined. Please provide a file for PROGRAM.")
endif

compile: check-program
	@if [ -f $(CODES_DIR)/$(PROGRAM).cpp ]; then \
		$(CC) $(CFLAGS) -o $(PROGRAM) $(CODES_DIR)/$(PROGRAM).cpp; \
	elif [ -f $(CODES_DIR)/$(PROGRAM).c ]; then \
		$(CPP) $(CFLAGS) -o $(PROGRAM) $(CODES_DIR)/$(PROGRAM).c; \
	fi

trace-program: check-program
	./$(DYNAMORIO_DIR)/bin64/drrun -root $(DYNAMORIO_DIR) \
	-t drcachesim -offline \
	-outdir $(TRACE_DIR)/ \
	-- $(PROGRAM)

# Launch a complete program
launch: 
	mkdir -p $(SIMULATION_OUTPUTS)
	python3 $(SCARAB_DIR)/bin/scarab_launch.py --program $(PROGRAM) \
	--params $(PARAM) --simdir $(SIMULATION_OUTPUTS) \
	--scarab_args='--$(SCARAB_ARGS) --pintool_args'--$(PINTOOL_ARGS)

launch-traces: check-param
	mkdir -p $(SIMULATION_OUTPUTS)
	cp $(PARAM) PARAMS.in 
	./$(SCARAB_DIR)/src/scarab --frontend memtrace --fetch_off_path_ops 0 \
	--cbp_trace_r0=$(TRACE_DIR) --sim_limit=$(SIMULATION_INSTRUCTIONS) \
	--memtrace_modules_log=$(SIMULATION_OUTPUTS)
	rm PARAMS.in


clean:
	find . -type f ! -name '*.cpp' ! -name 'Makefile' ! -name '*.py' \
	! -name '*.in' ! -name '*.c' -exec rm -f {} +
	rm -rf $(TRACE_DIR)/*.dir
	rm -rf $(SIMULATION_OUTPUTS)
