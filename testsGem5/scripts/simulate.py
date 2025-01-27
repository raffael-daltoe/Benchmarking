# simulate.py
import m5
from m5.objects import *
import os
from my_system import create_system
# Create the system
system = create_system()

#system.cpu.max_insts_any_thread = 6000

# Create the process
process = Process()

# Set up the binary path
thispath = os.path.dirname(os.path.realpath(__file__))
binpath = os.path.join(thispath, "../../", "conv")
process.cmd = [binpath]

# Set up the CPU workload
system.cpu.workload = process
system.cpu.createThreads()

# Set up system workload
system.workload = SEWorkload.init_compatible(binpath)

# Create root
root = Root(full_system=False, system=system)

# Instantiate the simulation
m5.instantiate()

print("Beginning simulation!")
exit_event = m5.simulate()
print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")