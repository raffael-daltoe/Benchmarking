import m5
from m5.objects import *
m5.util.addToPath("../../../../../")

from cache import *

class MySystem(System):
    def __init__(self):
        super(MySystem, self).__init__()
        
        # System configuration
        self.clk_domain = SrcClockDomain()
        self.clk_domain.clock = '4GHz'
        self.clk_domain.voltage_domain = VoltageDomain()
        
        self.mem_mode = 'timing'
        self.mem_ranges = [AddrRange('8GB')]
        
        # CPU configuration with adjusted parameters
        self.cpu = X86O3CPU()
        self.cpu.clk_domain = self.clk_domain
        
        # Core configuration
        self.cpu.numThreads = 1
        self.cpu.fetchWidth = 6   
        self.cpu.decodeWidth = 6
        self.cpu.dispatchWidth = 6
        self.cpu.issueWidth = 4
        self.cpu.wbWidth = 4
        self.cpu.commitWidth = 5
        
        # Buffer sizes
        self.cpu.numROBEntries = 352
        self.cpu.numIQEntries = 128
        self.cpu.LQEntries = 128
        self.cpu.SQEntries = 72
        
        # Pipeline stage configuration
        self.cpu.numPhysIntRegs = 256
        self.cpu.numPhysFloatRegs = 256
        self.cpu.numPhysVecRegs = 256
        self.cpu.numPhysCCRegs = 256
        
        # Branch Predictor
        self.cpu.branchPred = BiModeBP() 
        
        # Memory system
        self.membus = SystemXBar()
        
        # Interrupt controller setup
        self.cpu.createInterruptController()
        self.cpu.interrupts[0].pio = self.membus.mem_side_ports
        self.cpu.interrupts[0].int_requestor = self.membus.cpu_side_ports
        self.cpu.interrupts[0].int_responder = self.membus.mem_side_ports
        
        self._create_cache_hierarchy()
        self._setup_memory()
        self._connect_system()
        
    def _create_cache_hierarchy(self):
        # L1 caches
        self.cpu.icache = L1ICache()
        self.cpu.dcache = L1DCache()
        
        # L2 cache
        self.l2cache = L2Cache()
        
        # L3 Cache
        self.l3cache = L3Cache()
        
        self._setup_size_cache()
        self._setup_tlbs()
        
    def _setup_size_cache(self):
        
        self.cpu.icache.size = '256kB'
        self.cpu.icache.mshrs = 4
        self.cpu.icache.assoc = 8
        self.cpu.icache.tag_latency = 1
        self.cpu.icache.data_latency = 1
        self.cpu.icache.response_latency = 1
        #self.cpu.icache.prefetcher = NULL
        
        self.cpu.dcache.size = '256kB'
        self.cpu.dcache.assoc = 8 
        self.cpu.dcache.mshrs = 8
        self.cpu.dcache.tag_latency = 1
        self.cpu.dcache.data_latency = 1
        self.cpu.dcache.response_latency = 1
        #self.cpu.dcache.prefetcher = NULL
        
        self.l2cache.size = '256kB'
        self.l2cache.assoc = 8
        self.l2cache.mshrs = 16
        self.l2cache.tag_latency = 10
        self.l2cache.data_latency = 10
        self.l2cache.response_latency = 10
        #self.l2cache.prefetcher = NULL

        self.l3cache.size = '2MB'
        self.l3cache.assoc = 16
        self.l3cache.mshrs = 32
        self.l3cache.tag_latency = 10
        self.l3cache.data_latency = 10
        self.l3cache.response_latency = 10
        self.l3cache.replacement_policy = BRRIPRP()
        #self.l3cache.prefetcher = TaggedPrefetcher()

    def _setup_tlbs(self):
        self.cpu.itlb = X86TLB()
        self.cpu.dtlb = X86TLB()
        self.cpu.itlb.size = 64
        self.cpu.dtlb.size = 64
        self.cpu.itlb.entry_type = 'instruction'
        self.cpu.dtlb.entry_type = 'data'

    def _setup_memory(self):
        self.mem_ctrl = MemCtrl()
        self.mem_ctrl.dram = DDR4_2400_8x8()
        self.mem_ctrl.dram.tRP = '40ns'      
        self.mem_ctrl.dram.tRCD = '40ns'
        self.mem_ctrl.dram.tCS = '40ns'
        self.mem_ctrl.dram.ranks_per_channel = 1
        self.mem_ctrl.dram.banks_per_rank = 8
        self.mem_ctrl.dram.range = self.mem_ranges[0]
        
    def _connect_system(self):
        # Create buses
        self.l2bus = L2XBar()
        self.l3bus = L2XBar()
        
        # Connect L1 caches
        self.cpu.icache.connectCPU(self.cpu)
        self.cpu.dcache.connectCPU(self.cpu)
        
        # Connect L1 to L2 bus
        self.cpu.icache.connectBus(self.l2bus)
        self.cpu.dcache.connectBus(self.l2bus)
        
        # Connect L2 cache
        self.l2cache.cpu_side = self.l2bus.mem_side_ports
        self.l2cache.mem_side = self.l3bus.cpu_side_ports
        
        # Connect L3 cache
        self.l3cache.cpu_side = self.l3bus.mem_side_ports
        self.l3cache.mem_side = self.membus.cpu_side_ports
        
        # Connect memory controller
        self.mem_ctrl.port = self.membus.mem_side_ports
        
        # System port
        self.system_port = self.membus.cpu_side_ports


def create_system():
    system = MySystem()
    return system