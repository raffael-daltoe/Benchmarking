# Author: Raffael Rocha Daltoe
# Polytech Montpellier - 2024

CC = gcc
CPP = g++
CFLAGS = -O0

SCARAB_DIR = ../tools/scarab
DYNAMORIO_DIR = $(SCARAB_DIR)/src/deps/dynamorio
CODES_DIR = codes
BINARY_DIR = $(CODES_DIR)/binaries
SIM_OUT = simulations
PARAM_DIR = param
TRACE_DIR = traces

PARAM ?=
PROGRAM ?=

# PARAMETERS TO CHANGE FOR PYTHON SCRIPT
#####################################################

ENABLE_ASLR  ?=
SCARAB_ARGS  ?=
PINTOOL_ARGS ?=
WARMUP_INSTRUCTIONS     = 50000000 
SIMULATION_INSTRUCTIONS = 600000000

#####################################################

.PHONY: trace-program launch launch-trace launch-all

# Default target
all: compile check-param launch-trace

check-param:
ifeq ($(strip $(PARAM)),)
	@echo "Param config not defined, using the standard in $(PARAM_DIR)/"
	$(eval PARAM := $(PARAM_DIR)/PARAMS.in)
#	$(error "PARAM config is not defined. Please provide a file for PARAM.")
endif

compile: 
	@mkdir -p $(BINARY_DIR)
	@if [ -z "$(strip $(PROGRAM))" ]; then \
		echo "No PROGRAM specified, compiling all source files in $(CODES_DIR)"; \
		for file in $(CODES_DIR)/*.c $(CODES_DIR)/*.cpp; do \
			[ -e "$$file" ] || continue; \
			base_file=$$(basename "$$file"); \
			case "$$file" in \
				*.cpp) \
					echo "Compiling $$base_file with g++..."; \
					$(CPP) $(CFLAGS) -o $(BINARY_DIR)/$${base_file%.cpp} "$$file"; \
					;; \
				*.c) \
					echo "Compiling $$base_file with gcc..."; \
					$(CC) $(CFLAGS) -o $(BINARY_DIR)/$${base_file%.c} "$$file"; \
					;; \
			esac; \
		done; \
	else \
		if [ -f $(CODES_DIR)/$(PROGRAM).cpp ]; then \
			echo "Compiling $(PROGRAM).cpp with g++..."; \
			$(CPP) $(CFLAGS) -o $(BINARY_DIR)/$(PROGRAM) $(CODES_DIR)/$(PROGRAM).cpp; \
		elif [ -f $(CODES_DIR)/$(PROGRAM).c ]; then \
			echo "Compiling $(PROGRAM).c with gcc..."; \
			$(CC) $(CFLAGS) -o $(BINARY_DIR)/$(PROGRAM) $(CODES_DIR)/$(PROGRAM).c; \
		else \
			echo "Source file for $(PROGRAM) not found in $(CODES_DIR)"; \
			exit 1; \
		fi; \
	fi


trace-program:
	@mkdir -p $(TRACE_DIR)
	@if [ -z "$(strip $(PROGRAM))" ]; then \
		for bin in $(BINARY_DIR)/*; do \
			[ -e "$$bin" ] || continue; \
			base_file=$$(basename $$bin); \
			echo "Generating trace for $$base_file program"; \
			./$(DYNAMORIO_DIR)/bin64/drrun -root $(DYNAMORIO_DIR) \
				-t drcachesim -offline \
				-outdir $(TRACE_DIR) \
				-cores 1 \
				-jobs 32 \
				-exit_after_tracing $(SIMULATION_INSTRUCTIONS) \
				-- $$bin; \
			( cd $(TRACE_DIR) && \
			  bash ../convert-trace/run_portabilize_trace.sh > /dev/null 2>&1 && \
			  bash ../convert-trace/run_update_trace.sh > /dev/null 2>&1 ); \
			echo "Finished the trace for $$base_file"; \
		done; \
	else \
		echo "Generating trace for $(PROGRAM)..."; \
		./$(DYNAMORIO_DIR)/bin64/drrun -root $(DYNAMORIO_DIR) \
			-t drcachesim -offline \
			-outdir $(TRACE_DIR) \
			-- $(BINARY_DIR)/$(PROGRAM); \
		( cd $(TRACE_DIR) && \
		  bash ../convert-trace/run_portabilize_trace.sh > /dev/null 2>&1 && \
		  bash ../convert-trace/run_update_trace.sh > /dev/null 2>&1 ); \
		echo "Finished the trace for $(PROGRAM)"; \
	fi


# Launch a complete program
launch: compile
	@mkdir -p $(SIM_OUT)
	@python3 $(SCARAB_DIR)/bin/scarab_launch.py --program $(PROGRAM) \
	--params $(PARAM) --simdir $(SIM_OUT) \
	--scarab_args='--$(SCARAB_ARGS) --pintool_args'--$(PINTOOL_ARGS)

launch-trace: check-param
	@mkdir -p simulations/$(SIM_OUT)
	@cp $(PARAM) PARAMS.in 
	@TRACE_DIR_PATH=$(shell cd $(TRACE_DIR) && find . -maxdepth 1 -type d -name "drmemtrace.$(PROGRAM).*" | head -n 1) && \
	if [ -z "$$TRACE_DIR_PATH" ]; then \
		echo "Error: Trace directory not found for program $(PROGRAM)"; \
		rm PARAMS.in; \
		exit 1; \
	fi && \
	./$(SCARAB_DIR)/src/scarab --frontend memtrace  \
	--cbp_trace_r0=$(TRACE_DIR)/$$TRACE_DIR_PATH/trace \
	--inst_limit=$(SIMULATION_INSTRUCTIONS) \
	--memtrace_modules_log=$(TRACE_DIR)/$$TRACE_DIR_PATH/bin \
	--output_dir=simulations/$(SIM_OUT)
	@rm PARAMS.in

launch-all: check-param
#	@mkdir -p simulations/
	@cp $(PARAM) PARAMS.in 
	@python3 scarab.py 10 $(SCARAB_DIR) $(TRACE_DIR) $(SIM_OUT) \
	$(SIMULATION_INSTRUCTIONS) $(WARMUP_INSTRUCTIONS) $(PARAM)
#	@rm PARAMS.in


clean_outputs:
	rm -rf simulations/*

clean: clean_outputs
	find . -type f ! -name '*.cpp' ! -name 'Makefile' ! -name '*.py' \
	! -name '*.in' ! -name '*.c' ! -name '*.sh' ! -name '*.bash' \
	! -name '*.md' -exec rm -f {} +
	rm -rf $(TRACE_DIR)
