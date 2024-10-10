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

PARAM ?=
PROGRAM ?=

# PARAMETERS TO CHANGE FOR PYTHON SCRIPT
#####################################################

ENABLE_ASLR  ?=
SCARAB_ARGS  ?=
PINTOOL_ARGS ?=
SIMULATION_INSTRUCTIONS = 396990

#####################################################

# Default target
all: compile check-param check-program launch-traces

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

trace-program: compile
	mkdir -p $(TRACE_DIR)
	./$(DYNAMORIO_DIR)/bin64/drrun -root $(DYNAMORIO_DIR) \
		-t drcachesim -offline \
		-outdir $(TRACE_DIR)/ \
		-- $(PROGRAM)
	cd $(TRACE_DIR) && \
	bash ../convert-trace/run_portabilize_trace.sh && \
	bash ../convert-trace/run_update_trace.sh


# Launch a complete program
launch: 
	mkdir -p $(SIMULATION_OUTPUTS)
	python3 $(SCARAB_DIR)/bin/scarab_launch.py --program $(PROGRAM) \
	--params $(PARAM) --simdir $(SIMULATION_OUTPUTS) \
	--scarab_args='--$(SCARAB_ARGS) --pintool_args'--$(PINTOOL_ARGS)

launch-traces: check-param
	@mkdir -p $(SIMULATION_OUTPUTS)
	@cp $(PARAM) PARAMS.in 
	# Find the correct trace directory for the program inside traces/
	@TRACE_DIR_PATH=$(shell cd $(TRACE_DIR) && find . -maxdepth 1 -type d -name "drmemtrace.$(PROGRAM).*" | head -n 1) && \
	if [ -z "$$TRACE_DIR_PATH" ]; then \
		echo "Error: Trace directory not found for program $(PROGRAM)"; \
		rm PARAMS.in; \
		exit 1; \
	fi && \
	./$(SCARAB_DIR)/src/scarab --frontend memtrace --fetch_off_path_ops 0 \
	--cbp_trace_r0=$(TRACE_DIR)/$$TRACE_DIR_PATH/trace \
	--inst_limit=$(SIMULATION_INSTRUCTIONS) \
	--memtrace_modules_log=$(TRACE_DIR)/$$TRACE_DIR_PATH/bin
	@rm PARAMS.in





clean:
	find . -type f ! -name '*.cpp' ! -name 'Makefile' ! -name '*.py' \
	! -name '*.in' ! -name '*.c' ! -name '*.sh' ! -name '*.bash' \
	-exec rm -f {} +
	rm -rf $(TRACE_DIR)/*.dir
	rm -rf $(SIMULATION_OUTPUTS)
