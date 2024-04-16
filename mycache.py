import time
import random

# Helper functions
def log2(x):
    return (x).bit_length() - 1

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

def print_stats(l1, l2):
    l1_hits, l1_misses = l1.get_stats()
    l2_hits, l2_misses = l2.get_stats()
    
    print(f"L1 cache hits: {l1_hits}")
    print(f"L1 cache misses: {l1_misses}")
    print(f"L2 cache hits: {l2_hits}")
    print(f"L2 cache misses: {l2_misses}")
    

class Line:
    def __init__(self):
        self.tag = 0
        self.data = 0
        self.valid = False
        self.dirty = False

    def put(self, tag, data):
        self.tag = tag
        self.data = data
        self.valid = True
        self.dirty = False

    
    def remove(self):
        self.tag = 0
        self.data = 0
        self.valid = False
        self.dirty = False


    def __eq__(self, tag: int) -> bool:
        return self.tag == tag

    def isValid(self):
        return self.valid
    
    def isDirty(self):
        return self.dirty
    
    
# Cache simulation
class Cache:
    def __init__(self, capacity, line_size, assoc):
        self.capacity = capacity
        self.line_size = line_size
        self.assoc = assoc
        self.num_sets = capacity // (line_size * assoc)
        
        self.n_tag_bits = 32 - int(log2(self.num_sets)) - int(log2(self.line_size))
        self.n_s_bits = int(log2(self.num_sets))
        self.n_offset_bits = int(log2(self.line_size))
        
        array = [[None for _ in range(assoc)] for _ in range(self.num_sets)]
        for i in range(self.num_sets):
            for j in range(assoc):
                array[i][j] = Line()
        
        self.data = array
        self.next_cache = None
        
        self.hits = 0
        self.misses = 0
        self.energy_consumption = 0
    
    def get_energy_consumption(self):
        return self.energy_consumption
    
    def set_next_cache(self, next_cache):
        self.next_cache = next_cache
        
    def get_line(self, set_index, way):
        return self.data[set_index][way]
    
    def size(self):
        print("cache dim:", len(self.data[0]), len(self.data))
        print("cache size:", self.capacity)
        print("num sets:", self.num_sets)
    
    def get_stats(self):
        return self.hits, self.misses

    def access(self, address, op):
        # other_set_index = (address >> self.n_s_bits) % self.num_sets
        set_index = (address >> self.n_s_bits) & ((1 << self.n_s_bits) - 1)
        tag = address >> (int(log2(self.line_size)) + int(log2(self.num_sets)))
        
        # print(hex(address))
        # print(hex(set_index))

        # Check for hit
        empty_line = -1
        for way in range(self.assoc):
            line = self.data[set_index][way]
            if (not line.isValid()):
                empty_line = way
                continue
            
            if (line == tag):
                self.hits += 1
                return True

        # Cache miss
        self.misses += 1
        victim_way_index = random.randint(0, self.assoc - 1) if (empty_line == -1) else empty_line  # Random replacement policy
        if (self.data[set_index][victim_way_index].isDirty()):
            # have to calculate time and energy for writing back to main memory
            pass
        
        self.data[set_index][victim_way_index].remove()
        
        self.next_cache.access(address, op) # assume we can get from next memory layer (l2, main memory)
        self.data[set_index][victim_way_index].put(tag, "data") # put data in cache
        
        return False

# DRAM simulation
class DRAM:
    def __init__(self, size):
        self.size = size
        self.hits = 0
        self.misses = 0
        self.energy_consumption = 0
        
    def get_stats(self):
        return self.hits, self.misses
    
    def get_energy_consumption(self):
        return self.energy_consumption

    def access(self, address, op):
        self.hits += 1
        return True

    
# Memory subsystem parameters
# L1_ACCESS_TIME = 0.5  # 0.5 ns
# L2_ACCESS_TIME = 5  # 5 ns
# DRAM_ACCESS_TIME = 50  # 50 ns

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

class SIM:
    def __init__(self):
        self.total_energy_cost = 0 # pico joules
        self.time = 0 # p sec
        self.total_accesses = 0
        self.total_access_time = 0
        
        self.prev_stats = {"instr_l1_hits": 0, "instr_l1_misses": 0, "data_l1_hits": 0, "data_l1_misses": 0, "l2_hits": 0, "l2_misses": 0, "mem_hits": 0}
        
        # capacity, line_size, assoc
        self.instr_l1 = Cache(L1_CACHE_SIZE, CACHE_LINE_SIZE, L1_ASSOC) # 32 KB
        self.data_l1 = Cache(L1_CACHE_SIZE, CACHE_LINE_SIZE, L1_ASSOC) # 32 KB
        self.l2 = Cache(L1_CACHE_SIZE, CACHE_LINE_SIZE, L1_ASSOC) # 256 KB
        self.mem = DRAM(DRAM_SIZE)
        
        self.instr_l1.set_next_cache(self.l2)
        self.data_l1.set_next_cache(self.l2)
        self.l2.set_next_cache(self.mem)
        
        # self.cs = CacheSimulator(self.instr_l1, self.mem)

    def get_avg_access_time(self):
        return self.total_access_time / self.total_accesses
    
    def update_stats(self):
        l1_hit = False
        l2_hit = False
        missed = False
        
        instr_l1_hits, instr_l1_misses = self.instr_l1.get_stats()
        data_l1_hits, data_l1_misses = self.data_l1.get_stats()
        l2_hits, l2_misses = self.l2.get_stats()
        memory_hits, _ = self.mem.get_stats()
        
        l1_hit = instr_l1_hits > self.prev_stats["instr_l1_hits"] or data_l1_hits > self.prev_stats["data_l1_hits"]
        l2_hit = l2_hits > self.prev_stats["l2_hits"]
        missed = memory_hits > self.prev_stats["mem_hits"]
        
        # update prev stats
        self.prev_stats["instr_l1_hits"] = instr_l1_hits
        self.prev_stats["instr_l1_misses"] = instr_l1_misses
        self.prev_stats["data_l1_hits"] = data_l1_hits
        self.prev_stats["data_l1_misses"] = data_l1_misses
        self.prev_stats["l2_hits"] = l2_hits
        self.prev_stats["l2_misses"] = l2_misses
        self.prev_stats["mem_hits"] = memory_hits
        
        return l1_hit, l2_hit, missed
    
    def show_sim_data(self):
        print(f"Total Accesses: {self.total_accesses}")
        print(f"Total Time: {self.time} pico seconds")
        print(f"Average Access Time: {self.get_avg_access_time()} pico seconds")
        print(f"Total Energy Cost: {self.total_energy_cost} pico joules")
        print(f"L1 Hits: {self.prev_stats['instr_l1_hits'] + self.prev_stats['data_l1_hits']}")  # sum of instr and data l1 hits
        print(f"L2 Hits: {self.prev_stats['l2_hits']}")
        print(f"Misses: {self.prev_stats['mem_hits']}")
        
        
    def idle(self):
        pass
        
    def flush_cache(self):
        # clear instruction l1
        for i in range(self.instr_l1.num_sets):
            for j in range(self.instr_l1.assoc):
                self.instr_l1.data[i][j].remove()

        # clear data l1
        for i in range(self.data_l1.num_sets):
            for j in range(self.data_l1.assoc):
                self.data_l1.data[i][j].remove()
        
        # clear l2
        for i in range(self.l2.num_sets):
            for j in range(self.l2.assoc):
                self.l2.data[i][j].remove()
    
    def execute(self, address, op, value):
        if (op == 0):
            # Memory read
            self.data_l1.access(address)
        elif (op == 1):
            # Memory write
            self.data_l1.access(address)
        elif (op == 2):
            # Instruction fetch
            self.instr_l1.access(address)
        elif (op == 3):
            # Ignore
            self.idle()
        elif (op == 4):
            # Flush Cache
            self.flush_cache()
            
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
            time_passed = 0.5  # nsec
            energy_consumed = L1_IDLE_POWER * time_passed # l1 idle energy
            energy_consumed += L2_IDLE_POWER * time_passed # l2 idle energy
            energy_consumed += DRAM_IDLE_POWER * time_passed # dram idle energy
                    
        elif (l1_hit):
            # if l1 hit
            time_passed = L1_ACCESS_TIME # l1 access time
            energy_consumed = L1_READ_WRITE_POWER * time_passed # l1 access energy
            energy_consumed += L2_IDLE_POWER * time_passed # l2 idle energy
            energy_consumed += DRAM_IDLE_POWER * time_passed # dram idle energy
            
        elif (l2_hit):
            # if l2 hit
            time_passed = L2_ACCESS_TIME # l2 access time
            energy_consumed = L2_READ_WRITE_POWER * time_passed # l2 access energy 
            energy_consumed += L2_TRANSFER_ENERGY # l2 transfer energy
            energy_consumed += L1_IDLE_POWER * time_passed # l1 idle
            energy_consumed += DRAM_IDLE_POWER * time_passed # dram idle energy
        
        else:
            # both miss
            time_passed = DRAM_ACCESS_TIME # dram access time
            energy_consumed = DRAM_READ_WRITE_POWER * time_passed # dram access energy
            energy_consumed += DRAM_TRANSFER_ENERGY # dram transfer energy
            energy_consumed += L2_TRANSFER_ENERGY # l2 transfer energy
            energy_consumed += L2_IDLE_POWER * time_passed # l2 idle energy
            energy_consumed += L1_IDLE_POWER * time_passed # l1 idle energy

        self.total_accesses += 1
        self.time += time_passed
        self.total_energy_cost += energy_consumed
        
        pass
        

def main():
    simulator = SIM()
    file_path = "Traces/Spec_Benchmark/008.espresso.din"
    parsed_data = parse_trace_file(file_path)
    
    for op, address, value in parsed_data:
        # print(f"OP: {op}, Address: {address}, Value: {value}")
        simulator.execute(address, op, value)
        simulator.step()

        # break
    
    simulator.show_sim_data()

if __name__ == "__main__":
    main()
