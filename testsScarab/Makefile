# Author: Raffael Rocha Daltoe
# Polytech Montpellier - 2024

CC = g++
CFLAGS =

SCARAB_DIR = ../tools/scarab
CODES_DIR = codes
TRACES_DIR = traces
SIMULATION_OUTPUTS = sim_outputs
PARAM_DIR = param

PARAM ?=
PROGRAM ?=

# PARAMETERS TO CHANGE FOR PYTHON SCRIPT
#####################################################

ENABLE_ASLR  ?=
SCARAB_ARGS  ?=
PINTOOL_ARGS ?=

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

compile: check-param check-param
	@if [ -f $(CODES_DIR)/$(PROGRAM).cpp ]; then \
		$(CC) $(CFLAGS) -o $(PROGRAM) $(CODES_DIR)/$(PROGRAM).cpp; \
	fi

# Launch a complete program
launch: 
	python3 $(SCARAB_DIR)/bin/scarab_launch.py --program $(PROGRAM) \
	--params $(PARAM) --simdir $(SIMULATION_OUTPUTS) \
	--scarab_args='--$(SCARAB_ARGS) --pintool_args'--$(PINTOOL_ARGS)


clean:
	find . -type f ! -name '*.cpp' ! -name 'Makefile' ! -name '*.py' \
	! -name '*.in' -exec rm -f {} +
	rm -f $(SIMULATION_OUTPUTS)/*
