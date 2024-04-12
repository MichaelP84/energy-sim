import time

# this is the program generated by the LLM Claude, if we need to switch to implementing cache ourselves this could be useful, it is still kind of wrong though

# Memory subsystem parameters
L1_CACHE_SIZE = 32768  # 32 KB
L2_CACHE_SIZE = 262144  # 256 KB
DRAM_SIZE = 8 * 1024 * 1024 * 1024  # 8 GB
CACHE_LINE_SIZE = 64  # 64 bytes
L1_ACCESS_TIME = 0.5  # 0.5 ns
L2_ACCESS_TIME = 5  # 5 ns
DRAM_ACCESS_TIME = 50  # 50 ns
L1_IDLE_POWER = 0.5  # 0.5 W
L1_READ_WRITE_POWER = 1  # 1 W
L2_IDLE_POWER = 0.8  # 0.8 W
L2_READ_WRITE_POWER = 2  # 2 W
L2_TRANSFER_ENERGY = 5  # 5 pJ
DRAM_IDLE_POWER = 0.8  # 0.8 W
DRAM_READ_WRITE_POWER = 4  # 4 W
DRAM_TRANSFER_ENERGY = 640  # 640 pJ
CPU_CLOCK_SPEED = 2  # 2 GHz

# Cache simulation
class Cache:
    def __init__(self, size, line_size, assoc):
        self.size = size
        self.line_size = line_size
        self.assoc = assoc
        self.num_sets = size // (line_size * assoc)
        self.tag_bits = 64 - int(log2(self.num_sets)) - int(log2(self.line_size))
        self.directory = [[None] * assoc for _ in range(self.num_sets)]
        self.data = [[None] * assoc for _ in range(self.num_sets)]
        self.hits = 0
        self.misses = 0

    def access(self, address, op):
        set_index = (address >> int(log2(self.line_size))) % self.num_sets
        tag = address >> (int(log2(self.line_size)) + int(log2(self.num_sets)))

        # Check for hit
        for way in range(self.assoc):
            if self.directory[set_index][way] == tag:
                self.hits += 1
                if op == 0:  # Read
                    return True, self.data[set_index][way]
                else:  # Write
                    self.data[set_index][way] = [0] * (self.line_size // 4)
                    return True, self.data[set_index][way]

        # Cache miss
        self.misses += 1
        victim_way = 0  # Random replacement policy
        if self.directory[set_index][victim_way] is not None:
            # Evict the victim line
            pass  # Implement eviction logic

        # Bring the line from the next level of the hierarchy
        self.directory[set_index][victim_way] = tag
        self.data[set_index][victim_way] = [0] * (self.line_size // 4)
        if op == 0:  # Read
            return False, self.data[set_index][victim_way]
        else:  # Write
            self.data[set_index][victim_way] = [0] * (self.line_size // 4)
            return False, self.data[set_index][victim_way]

# DRAM simulation
class DRAM:
    def __init__(self, size):
        self.size = size
        self.read_write_energy = 0
        self.idle_energy = 0

    def access(self, address, op):
        self.read_write_energy += DRAM_TRANSFER_ENERGY
        if op == 0:  # Read
            self.read_write_energy += DRAM_READ_WRITE_POWER * DRAM_ACCESS_TIME / 1e9
            return [0] * (CACHE_LINE_SIZE // 4)
        else:  # Write
            self.read_write_energy += DRAM_READ_WRITE_POWER * DRAM_ACCESS_TIME / 1e9
            return [0] * (CACHE_LINE_SIZE // 4)
        self.idle_energy += DRAM_IDLE_POWER * DRAM_ACCESS_TIME / 1e9

# Main simulation loop
def simulate_memory_subsystem(trace_file):
    with open(trace_file, 'r') as f:
        trace = [line.strip().split() for line in f]

    l1_cache = Cache(L1_CACHE_SIZE, CACHE_LINE_SIZE, 1)
    l2_cache = Cache(L2_CACHE_SIZE, CACHE_LINE_SIZE, 4)
    dram = DRAM(DRAM_SIZE)
    total_time = 0
    total_energy = 0

    for line in trace:
        op = int(line[0])
        address = int(line[1], 16)
        start_time = time.time()

        if op == 0 or op == 1:  # Read or write
            l1_hit, l1_data = l1_cache.access(address, op)
            if l1_hit:
                total_time += L1_ACCESS_TIME / 1e9
                if op == 0:  # Read
                    total_energy += L1_READ_WRITE_POWER * L1_ACCESS_TIME / 1e9
                else:  # Write
                    total_energy += L1_READ_WRITE_POWER * L1_ACCESS_TIME / 1e9
            else:
                l2_hit, l2_data = l2_cache.access(address, op)
                if l2_hit:
                    total_time += L2_ACCESS_TIME / 1e9
                    if op == 0:  # Read
                        total_energy += L2_READ_WRITE_POWER * L2_ACCESS_TIME / 1e9
                    else:  # Write
                        total_energy += L2_READ_WRITE_POWER * L2_ACCESS_TIME / 1e9
                    total_energy += L2_TRANSFER_ENERGY / 1e12
                else:
                    dram_data = dram.access(address, op)
                    total_time += DRAM_ACCESS_TIME / 1e9
                    if op == 0:  # Read
                        total_energy += DRAM_READ_WRITE_POWER * DRAM_ACCESS_TIME / 1e9
                    else:  # Write
                        total_energy += DRAM_READ_WRITE_POWER * DRAM_ACCESS_TIME / 1e9
                    total_energy += DRAM_TRANSFER_ENERGY / 1e12
        elif op == 2:  # Instruction fetch
            l1_hit, l1_data = l1_cache.access(address, op)
            if l1_hit:
                total_time += L1_ACCESS_TIME / 1e9
                total_energy += L1_READ_WRITE_POWER * L1_ACCESS_TIME / 1e9
            else:
                l2_hit, l2_data = l2_cache.access(address, op)
                if l2_hit:
                    total_time += L2_ACCESS_TIME / 1e9
                    total_energy += L2_READ_WRITE_POWER * L2_ACCESS_TIME / 1e9
                    total_energy += L2_TRANSFER_ENERGY / 1e12
                else:
                    dram_data = dram.access(address, op)
                    total_time += DRAM_ACCESS_TIME / 1e9
                    total_energy += DRAM_READ_WRITE_POWER * DRAM_ACCESS_TIME / 1e9
                    total_energy += DRAM_TRANSFER_ENERGY / 1e12

        end_time = time.time()
        total_time += end_time - start_time

    print(f"L1 cache hits: {l1_cache.hits}")
    print(f"L1 cache misses: {l1_cache.misses}")
    print(f"L2 cache hits: {l2_cache.hits}")
    print(f"L2 cache misses: {l2_cache.misses}")
    print(f"Total energy consumption: {total_energy:.2f} J")
    print(f"Average memory access time: {total_time / len(trace) * 1e9:.2f} ns")

# Helper function
def log2(x):
    return (x).bit_length() - 1

# Example usage
simulate_memory_subsystem("Traces/Spec_Benchmark/008.espresso.din")