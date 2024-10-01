# Variables
CC = g++
CFLAGS =

CHAMPSIM_DIR = ../tools/ChampSim
TRACER_DIR = $(CHAMPSIM_DIR)/tracer
PIN_TRACER_DIR = $(TRACER_DIR)/pin
CVP_CONVERTER_DIR = $(TRACER_DIR)/cvp_converter
CODES_DIR = codes
TRACES_DIR = traces
SIMULATION_OUTPUTS = sim_outputs

SRC ?=

PIN = pin

OBJ-INTEL64 = $(PIN_TRACER_DIR)/obj-intel64/champsim_tracer.so
BIN_CHAMPSIM = $(CHAMPSIM_DIR)/bin/champsim

# PARAMETERS TO CHANGE FOR PYTHON SCRIPT
#####################################################

WARMUP_INSTRUCTIONS = 20000							
SIMULATION_INSTRUCTIONS = 500000

#####################################################

# Default target
all: check-src compile convert-pin trace

check-src:
ifeq ($(strip $(SRC)),)
	$(error "SRC variable is not defined. Please provide a value for SRC.")
endif

# Compile the program
compile: check-src
	$(CC) $(CFLAGS) -o $(SRC) $(CODES_DIR)/$(SRC).cpp

convert-pin: check-src
	@if [ -x $(SRC) ]; then \
		$(PIN) -t $(OBJ-INTEL64) -o $(TRACES_DIR)/$(SRC).champsimtrace -- \
		./$(SRC); \
	else \
		$(PIN) -t $(OBJ-INTEL64) -o $(TRACES_DIR)/$(SRC).champsimtrace -- \
		$(SRC); \
	fi
	xz -zf $(TRACES_DIR)/$(SRC).champsimtrace

trace: check-src
	$(BIN_CHAMPSIM) $(TRACES_DIR)/$(SRC).champsimtrace.xz > \
	$(SIMULATION_OUTPUTS)/$(SRC).txt

trace-all:
	python3 champsim.py $(nproc) $(CHAMPSIM_DIR) $(TRACES_DIR) \
	$(CHAMPSIM_DIR)/champsim_config.json $(SIMULATION_OUTPUTS) \
	$(WARMUP_INSTRUCTIONS) $(SIMULATION_INSTRUCTIONS)

clean:
	find . -type f ! -name '*.cpp' ! -name 'Makefile' ! -name '*.py' -exec rm -f {} +
	rm -f $(SIMULATION_OUTPUTS)/*

