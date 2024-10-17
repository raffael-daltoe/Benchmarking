# Author: Raffael Rocha Daltoe
# Polytech Montpellier - 2024

CC = gcc
CPP = g++
CFLAGS =

CHAMPSIM_DIR = ../tools/ChampSim
TRACER_DIR = $(CHAMPSIM_DIR)/tracer
PIN_TRACER_DIR = $(TRACER_DIR)/pin
CVP_CONVERTER_DIR = $(TRACER_DIR)/cvp_converter
CODES_DIR = codes
TRACES_DIR = traces
SIMULATION_OUTPUTS = sim_outputs
PARAM = param

SRC ?=

PIN = pin

OBJ-INTEL64 = $(PIN_TRACER_DIR)/obj-intel64/champsim_tracer.so
BIN_CHAMPSIM = $(CHAMPSIM_DIR)/bin/champsim

# PARAMETERS TO CHANGE FOR PYTHON SCRIPT
#####################################################

WARMUP_INSTRUCTIONS     = 20000					
SIMULATION_INSTRUCTIONS = 50000000

#####################################################

# Default target
all: check-src compile convert-pin trace

check-src:
ifeq ($(strip $(SRC)),)
	$(error "SRC variable is not defined. Please provide a value for SRC.")
endif

# Compile the program
compile: check-src
	@if [ -f $(CODES_DIR)/$(SRC).cpp ]; then \
		$(CC) $(CFLAGS) -o $(SRC) $(CODES_DIR)/$(SRC).cpp; \
	elif [ -f $(CODES_DIR)/$(SRC).c ]; then \
		$(CPP) $(CFLAGS) -o $(SRC) $(CODES_DIR)/$(SRC).c; \
	fi

convert-pin: check-src
	@mkdir -p $(TRACES_DIR)
	@if [ -x $(SRC) ]; then \
		$(PIN) -t $(OBJ-INTEL64) -o $(TRACES_DIR)/$(SRC).champsimtrace  \
		-t $(SIMULATION_INSTRUCTIONS) -- ./$(SRC); \
	else \
		$(PIN) -t $(OBJ-INTEL64) -o $(TRACES_DIR)/$(SRC).champsimtrace  \
		-t $(SIMULATION_INSTRUCTIONS) -- $(SRC); \
	fi
	xz -zf $(TRACES_DIR)/$(SRC).champsimtrace

trace: check-src
	@mkdir -p $(SIMULATION_OUTPUTS)
	@$(BIN_CHAMPSIM) $(TRACES_DIR)/$(SRC).champsimtrace.xz > \
	$(SIMULATION_OUTPUTS)/$(SRC).txt \
	$(if $(SIMULATION_INSTRUCTIONS),--simulation_instructions $(SIMULATION_INSTRUCTIONS)) \
	$(if $(WARMUP_INSTRUCTIONS),--warmup_instructions $(WARMUP_INSTRUCTIONS))
	@echo "Simulation Finished"

trace-all:
	python3 champsim.py $(nproc) $(CHAMPSIM_DIR) $(TRACES_DIR) \
	$(PARAM)/champsim_config.json $(SIMULATION_OUTPUTS) \
	$(WARMUP_INSTRUCTIONS) $(SIMULATION_INSTRUCTIONS)

clean_outputs:
	rm -rf $(SIMULATION_OUTPUTS)

clean: clean_outputs
	find . -type f ! -name '*.cpp' ! -name '*.c' ! -name 'Makefile' \
	! -name '*.py' ! -name '*.md' -exec rm -f {} +

#python3 champsim.py 32 ../tools/ChampSim traces ../tools/ChampSim/champsim_config.json sim_outputs 10000 5000000000 ; make SRC=cache ; python3 champsim.py 32 ../tools/ChampSim traces ../tools/ChampSim/champsim_config.json sim_outputs 10000 5000000000