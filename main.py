from cachesim import CacheSimulator, Cache, MainMemory

# The memory subsystem consists of an L1 cache, an L2 cache, and DRAM. 
# The L1 cache is direct mapped and has a 32KB for instruc6ons and 32KB for data. 
# The L2 cache is set-associa6ve with set associa6vity of 4 and has a combined cache of 256KB.
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
        self.total_energy_cost = 0
        self.time = 0
        
        self.mem = MainMemory()
        self.l3 = Cache("L3", 20480, 16, 64, "LRU")  # 20MB: 20480 sets, 16-ways with cacheline size of 64 bytes
        self.mem.load_to(self.l3)
        self.mem.store_from(self.l3)
        self.l2 = Cache("L2", 512, 8, 64, "LRU", store_to=self.l3, load_from=self.l3)  # 256KB
        self.l1 = Cache("L1", 64, 8, 64, "LRU", store_to=self.l2, load_from=self.l2)  # 32KB
        self.cs = CacheSimulator(self.l1, self.mem)

    def load(self, addr):
        self.cs.load(addr)  # Loads one byte from address 2342, should be a miss in all cache-levels

    def store(self, addr, length):
        self.cs.store(addr, length)  # Stores 8 bytes to addresses 512-519,
                            # will also be a load miss (due to write-allocate)

    def load(self, addr, length):
        self.cs.load(addr, length)  # Loads from address 512 until (exclusive) 520 (eight bytes)

    def force_write_back(self):
        self.cs.force_write_back()

    def print_stats(self):
        self.cs.print_stats()


def main():

    # mem = MainMemory()
    # l3 = Cache("L3", 20480, 16, 64, "LRU")  # 20MB: 20480 sets, 16-ways with cacheline size of 64 bytes
    # mem.load_to(l3)
    # mem.store_from(l3)
    # l2 = Cache("L2", 512, 8, 64, "LRU", store_to=l3, load_from=l3)  # 256KB
    # l1 = Cache("L1", 64, 8, 64, "LRU", store_to=l2, load_from=l2)  # 32KB
    # cs = CacheSimulator(l1, mem)

    # cs.load(2342)  # Loads one byte from address 2342, should be a miss in all cache-levels
    # cs.store(512, length=8)  # Stores 8 bytes to addresses 512-519,
    #                         # will also be a load miss (due to write-allocate)
    # cs.load(512, length=8)  # Loads from address 512 until (exclusive) 520 (eight bytes)

    # cs.force_write_back()
    # cs.print_stats()
    
    file_path = "Traces/Spec_Benchmark/008.espresso.din"
    parsed_data = parse_trace_file(file_path)
    # for op, address, value in parsed_data:
    #     print(f"OP: {op}, Address: {address}, Value: {value}")
    #     break

if __name__ == "__main__":
    main()