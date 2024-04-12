from cachesim import CacheSimulator, Cache, MainMemory

# The memory subsystem consists of an L1 cache, an L2 cache, and DRAM. 
# The L1 cache is direct mapped and has a 32KB for instructions and 32KB for data. 
# The L2 cache is set-associative with set associativity of 4 and has a combined cache of 256KB.
# The cache replacement algorithm is Random.
# The DRAM consists of an 8GB DDR-5 DIMM. 
# Data access to main memory is done in units of 64 bytes, and the cache line size is 64 bytes (both L1 and L2).

# The read/write access times are:
# L1 cache: 0.5nsec
# L2 cache: 5nsec
# DRAM: 50nsec

# The power consumption of the caches and DRAM are given below:
# L1 cache: 0.5W idle and 1W during reads or writes.
# L2 cache: 0.8W idle and 2W during reads or writes. In addition, accessing the L2 cache will incur a 5pJ to account for the data transfer between the L1 and the L2.
# DRAM: 0.8W idle increasing to 4W during reads and writes. In addition, accessing the memory will add a penalty of 640pJ for every access 
# (to account for the energy necessary for data transfer and accessing the bus).

# You can assume that the processor runs at2GHz (0.5nsec cycle time)
# For all memory accesses and also the idle time, you need to record the energy consumed by the L1, L2 and the memory.

L1_CACHE_SIZE = 32768  # 32 KB
L2_CACHE_SIZE = 262144  # 256 KB
DRAM_SIZE = 8 * 1024 * 1024 * 1024  # 8 GB
CACHE_LINE_SIZE = 64  # 64 bytes

L1_ASSOC = 1
L1_SETS = L1_CACHE_SIZE // (CACHE_LINE_SIZE * L1_ASSOC) # S = C / (A * B)
L2_ASSOC = 4
L2_SETS = L2_CACHE_SIZE // (CACHE_LINE_SIZE * L2_ASSOC)

L1_ACCESS_TIME = 0.5 * 1000   # 0.5 ns or 500 ps
L2_ACCESS_TIME = 5 * 1000  # 5 ns
DRAM_ACCESS_TIME = 50 * 1000  # 50 ns

L1_IDLE_POWER = 0.5  # 0.5 W (picojoule / picosecond)
L1_READ_WRITE_POWER = 1  # 1 W
L2_IDLE_POWER = 0.8  # 0.8 W
L2_READ_WRITE_POWER = 2  # 2 W
DRAM_IDLE_POWER = 0.8  # 0.8 W
DRAM_READ_WRITE_POWER = 4  # 4 W

L2_TRANSFER_ENERGY = 5  # 5 pJ
DRAM_TRANSFER_ENERGY = 640  # 640 pJ

CPU_CLOCK_SPEED = 2  # 2 GHz

def parse_trace_file(file_path):
    parsed_data = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip().split()
            if len(line) == 3:
                op = int(line[0])
                address = int(line[1], 16)  # Convert hexadecimal address to integer
                value = int(line[2], 16)    # Convert hexadecimal value to integer
                parsed_data.append((op, address, value))
    return parsed_data

class SIM:
    def __init__(self):
        self.total_energy_cost = 0 # pico joules
        self.time = 0 # p sec
        self.l1_hits = 0
        self.l2_hits = 0
        self.misses = 0
        
        self.prev_stats = None
        
        self.l2 = Cache("L2", L2_SETS, L2_ASSOC, CACHE_LINE_SIZE, "RR") # 256KB
        self.instr_l1 = Cache("L1", L1_SETS, L1_ASSOC, CACHE_LINE_SIZE, "RR", store_to=self.l2, load_from=self.l2)  # 32KB
        # self.data_l1 = Cache("L1", 64, 8, CACHE_LINE_SIZE, "RR", store_to=self.l2, load_from=self.l2)  # 32KB
        self.mem = MainMemory()
        self.mem.load_to(self.l2)
        self.mem.store_from(self.l2)
        self.cs = CacheSimulator(self.instr_l1, self.mem)

    def load(self, addr):
        self.cs.load(addr)  # Loads one byte from address 2342, should be a miss in all cache-levels

    def store(self, addr, length):
        self.cs.store(addr, length)  

    def update_stats(self):
        stats = self.cs.print_stats()
        l1_hit = False
        l2_hit = False
        missed = False
        
        for level in stats:
            if (level['name'] == "L1"):
                if level['HIT_count'] > self.l1_hits:
                    l1_hit = True
                    self.l1_hits = level['HIT_count']
            elif (level['name'] == "L2"):
                if level['HIT_count'] > self.l2_hits:
                    l2_hit = True
                    self.l2_hits = level['HIT_count']
        
        if (not l1_hit and not l2_hit):
            self.misses += 1
            missed = True
        
        return l1_hit, l2_hit, missed
    
    def show_sim_data(self):
        print(f"Total Energy Cost: {self.total_energy_cost} pico joules")
        print(f"Total Time: {self.time} pico seconds")
        print(f"L1 Hits: {self.l1_hits}")
        print(f"L2 Hits: {self.l2_hits}")
        print(f"Misses: {self.misses}")
        
        
    def idle(self):
        pass
    
    def flush_cache(self):
        pass
        
    def step(self):
        # for each action, check current state with previous stats to see what happened
        l1_hit, l2_hit, missed = self.update_stats()
        
        time_passed = 0
        energy_consumed = 0
        
        assert(not (l1_hit and l2_hit))
        assert(not (l1_hit and missed))
        assert(not (l2_hit and missed))
        
        # if l1 missed, l2 missed, and didnt miss, then this was idle instruction
        if (not l1_hit and not l2_hit and not missed):
            time_passed = 0.5  #nsec
                    
        elif (l1_hit):
            # if l1 hit
            # l1 access time, 
            time_passed = L1_ACCESS_TIME
            # l1 access energy
            energy_consumed = L1_READ_WRITE_POWER * time_passed
            # l2 idle energy
            energy_consumed += L2_IDLE_POWER * time_passed
            # dram idle energy
            energy_consumed += DRAM_IDLE_POWER * time_passed
            
        elif (l2_hit):
            # if l2 hit
            # l2 access time
            time_passed = L2_ACCESS_TIME
            # l2 access energy 
            energy_consumed = L2_READ_WRITE_POWER * time_passed
            # l2 transfer energy
            energy_consumed += L2_TRANSFER_ENERGY
            # l1 idle
            energy_consumed += L1_IDLE_POWER * time_passed
            # dram idle energy
            energy_consumed += DRAM_IDLE_POWER * time_passed
        
        else:
            # both miss
            # dram access time
            time_passed = DRAM_ACCESS_TIME
            # dram access energy
            energy_consumed = DRAM_READ_WRITE_POWER * time_passed
            # dram transfer energy
            energy_consumed += DRAM_TRANSFER_ENERGY
            # l2 transfer energy
            energy_consumed += L2_TRANSFER_ENERGY
            # l2 idle energy
            energy_consumed += L2_IDLE_POWER * time_passed
            # l1 idle energy
            energy_consumed += L1_IDLE_POWER * time_passed
                
        self.time += time_passed
        self.total_energy_cost += energy_consumed
        
        pass
        


def main():

    simulator = SIM()
    
    file_path = "Traces/Spec_Benchmark/008.espresso.din"
    parsed_data = parse_trace_file(file_path)
    for op, address, value in parsed_data:
        # print(f"OP: {op}, Address: {address}, Value: {value}")
        
        if (op == 0):
            # Memory read
            simulator.load(address)
        elif (op == 1):
            # Memory write
            simulator.store(address, value)
        elif (op == 2):
            # Instruction fetch
            simulator.load(address)
        elif (op == 3):
            # Ignore
            simulator.idle()
        elif (op == 4):
            # Flush Cache
            simulator.flush_cache()
            
        simulator.step()

        # break
    
    simulator.show_sim_data()
    
    
    

if __name__ == "__main__":
    main()