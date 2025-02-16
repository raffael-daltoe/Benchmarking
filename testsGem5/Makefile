CC = gcc
CPP = g++
CFLAGS = -O0

GEM5_DIR = ../tools/gem5
MY_SYSTEM_DIR = scripts/
CODES_DIR = codes
BINARY_DIR = $(CODES_DIR)/bin
SIMULATION_OUTPUTS = sim_outputs

PROGRAM ?= 
# PARAMETERS TO CHANGE FOR PYTHON SCRIPT
#####################################################

WARMUP_INSTRUCTIONS     =  
SIMULATION_INSTRUCTIONS = 600000000


#####################################################

# Compile the program for each provided SRC or all if none are specified
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

exec-all: compile
	@python3 gem5.py 8 $(GEM5_DIR) $(BINARY_DIR) \
	$(MY_SYSTEM_DIR) $(SIMULATION_OUTPUTS) \
	$(if $(filter-out 0,$(WARMUP_INSTRUCTIONS)),$(WARMUP_INSTRUCTIONS),none) \
	$(if $(filter-out 0,$(SIMULATION_INSTRUCTIONS)),$(SIMULATION_INSTRUCTIONS),none)

clean:
	rm -rf $(SIMULATION_OUTPUTS)
	rm -rf $(BINARY_DIR)