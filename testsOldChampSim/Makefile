# Author: Raffael Rocha Daltoe
# Polytech Montpellier - 2024

CC = gcc
CPP = g++
CFLAGS = -O0

CHAMPSIM_DIR = ../tools/ChampSim
TRACER_DIR = $(CHAMPSIM_DIR)/tracer
PIN_TRACER_DIR = $(TRACER_DIR)/pin
CVP_CONVERTER_DIR = $(TRACER_DIR)/cvp_converter
CODES_DIR = codes
BIN_DIR = $(CODES_DIR)/bin
TRACES_DIR = traces
SIMULATION_OUTPUTS = sim_outputs
PARAM = param
NPB_CPP_DIR = ../tools/NPB-CPP
NPB_SER_DIR = $(NPB_CPP_DIR)/NPB-SER 

SRC ?=

# For NPB-CPP
BENCHMARK ?=
WORKLOAD ?=


PIN = pin

OBJ-INTEL64 = $(PIN_TRACER_DIR)/obj-intel64/champsim_tracer.so
BIN_CHAMPSIM = $(CHAMPSIM_DIR)/bin/champsim

# PARAMETERS TO CHANGE FOR PYTHON SCRIPT
#####################################################

WARMUP_INSTRUCTIONS     = 50000000 
SIMULATION_INSTRUCTIONS = 600000000


#####################################################

# Default target
all: check-src compile convert-pin trace

check-src:
ifeq ($(strip $(SRC)),)
	$(error "SRC variable is not defined. Please provide a value for SRC.")
endif

# Compile the program for each provided SRC or all if none are specified
compile:
	@mkdir -p $(TRACES_DIR)
	@if [ -z "$(strip $(SRC))" ]; then \
		echo "SRC is not defined, using all files in $(CODES_DIR)"; \
		for file in $(CODES_DIR)/*; do \
			[ -e "$$file" ] || continue; \
			case "$$file" in \
				*.cpp) \
					base_file=$$(basename $$file .cpp); \
					echo "Compiling $$file as C++ source"; \
					$(CPP) $(CFLAGS) -o $$base_file $$file; \
					;; \
				*.c) \
					base_file=$$(basename $$file .c); \
					echo "Compiling $$file as C source"; \
					$(CC) $(CFLAGS) -o $$base_file $$file; \
					;; \
				*) \
					echo "Skipping unknown file type: $$file"; \
					;; \
			esac; \
		done; \
	else \
		for src in $(SRC); do \
			if [ -f $(CODES_DIR)/$$src.cpp ]; then \
				$(CPP) $(CFLAGS) -o $$src $(CODES_DIR)/$$src.cpp; \
			elif [ -f $(CODES_DIR)/$$src.c ]; then \
				$(CC) $(CFLAGS) -o $$src $(CODES_DIR)/$$src.c; \
			else \
				echo "Source file for $$src not found in $(CODES_DIR)"; \
				exit 1; \
			fi; \
		done; \
	fi

compile_from_NPB:
	@mkdir -p $(TRACES_DIR)
	cd $(NPB_SER_DIR) && \
	make $(BENCHMARK) CLASS=$(WORKLOAD) && \
	mv bin/$(BENCHMARK).$(WORKLOAD) ../../../testsOldChampSim/codes/bin/$(shell echo $(BENCHMARK)$(WORKLOAD) | tr '[:upper:]' '[:lower:]')

# Convert the program to Pin traces
convert-pin:
	@mkdir -p $(TRACES_DIR)
	@if [ -z "$(strip $(SRC))" ]; then \
		for file in $(BIN_DIR)/*; do \
			[ -e "$$file" ] || continue; \
			base_file=$$(basename $$file); \
			echo "Converting $$base_file to Pin trace..."; \
			$(PIN) -t $(OBJ-INTEL64) -o $(TRACES_DIR)/$$base_file.champsimtrace \
			-t $(SIMULATION_INSTRUCTIONS) -- ./$(BIN_DIR)/$$base_file; \
		done; \
	else \
		for src in $(SRC); do \
			echo "Converting $$src to Pin trace.."; \
			$(PIN) -t $(OBJ-INTEL64) -o $(TRACES_DIR)/$$src.champsimtrace \
			-t $(SIMULATION_INSTRUCTIONS) -- ./$$src; \
		done; \
	fi

trace: check-src
	@mkdir -p $(SIMULATION_OUTPUTS)
	@$(BIN_CHAMPSIM) $(TRACES_DIR)/$(SRC).champsimtrace.xz > \
	$(SIMULATION_OUTPUTS)/$(SRC).txt \
	$(SIMULATION_INSTRUCTIONS) \
	$(WARMUP_INSTRUCTIONS)
	@echo "Simulation Finished"

trace-all:
	@python3 champsim.py 11 $(CHAMPSIM_DIR) $(TRACES_DIR) \
	$(PARAM)/champsim_config.json $(SIMULATION_OUTPUTS) \
	$(if $(filter-out 0,$(WARMUP_INSTRUCTIONS)),$(WARMUP_INSTRUCTIONS),none) \
	$(if $(filter-out 0,$(SIMULATION_INSTRUCTIONS)),$(SIMULATION_INSTRUCTIONS),none)

clean_outputs:
	rm -rf $(SIMULATION_OUTPUTS)
	rm -rf $(CHAMPSIM_DIR)/json_files/
	rm -rf $(CHAMPSIM_DIR)/bin/

clean: clean_outputs
	find . -type f ! -name '*.cpp' ! -name '*.c' ! -name 'Makefile' \
	! -name '*.py' ! -name '*.md' ! -name '*.json' -exec rm -f {} +