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

# How much <warmup_instructions> and <simulation_instructions> below
#####################################################

WARMUP_INSTRUCTIONS = 20000							
SIMULATION_INSTRUCTIONS = 500000

#####################################################

# Default target
all: check-src compile trace

check-src:
ifeq ($(strip $(SRC)),)
	$(error "SRC variable is not defined. Please provide a value for SRC.")
endif

# Compile the program
compile: check-src
	$(CC) $(CFLAGS) -o $(CODES_DIR)/$(SRC) $(CODES_DIR)/$(SRC).cpp

trace: compile
	$(PIN) -t $(OBJ-INTEL64) -o $(TRACES_DIR)/$(SRC).champsimtrace -- \
	./$(CODES_DIR)/$(SRC)

	xz -zf $(TRACES_DIR)/$(SRC).champsimtrace
	$(BIN_CHAMPSIM) $(TRACES_DIR)/$(SRC).champsimtrace.xz

trace-all:
	python3 champsim.py $(nproc) $(CHAMPSIM_DIR) $(TRACES_DIR) \
	$(CHAMPSIM_DIR)/champsim_config.json $(SIMULATION_OUTPUTS) \
	$(WARMUP_INSTRUCTIONS) $(SIMULATION_INSTRUCTIONS)

clean:
	find $(CODES_DIR) -type f ! -name '*.cpp' -exec rm -f {} +
	rm -f $(SIMULATION_OUTPUTS)/*

