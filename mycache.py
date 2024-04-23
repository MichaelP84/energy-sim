import time
import random
import os

# How this simulator works
# 1. parse trace file
# 2. for each instruction, execute it
# 3. get all the hits, misses, and/or evictions that happened after the instruction executed and do calculations for time and energy based on what happened

# since there is different memory vs instruction l1 cache, while one is writing, is the other technically incurring idling energy or is the cost for both
# do we have to count the cost for just the checking if data is within the cache during the first part of a miss, and if so would this be the same energy cost?

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
    def __init__(self, capacity, line_size, assoc, access_time, idle_power, read_write_power, transfer_energy):
        self.capacity = capacity
        self.line_size = line_size
        self.assoc = assoc
        self.num_sets = capacity // (line_size * assoc)
        
        self.n_tag_bits = 32 - int(log2(self.num_sets)) - int(log2(self.line_size))
        self.n_s_bits = int(log2(self.num_sets))
        self.n_offset_bits = int(log2(self.line_size))
        
        # print("n_tag_bits:", self.n_tag_bits)
        # print("n_s_bits:", self.n_s_bits)
        # print("n_offset_bits:", self.n_offset_bits)
        
        # print("\n************")
        # print("Cache size:", self.capacity)
        # print("Line size:", self.line_size)
        # print("Associativity:", self.assoc)
        # print("Number of sets:", self.num_sets)
        
        array = [[None for _ in range(assoc)] for _ in range(self.num_sets)]
        for i in range(self.num_sets):
            for j in range(assoc):
                array[i][j] = Line()
        
        self.data = array
        self.next_cache = None
        
        self.hits = 0
        self.misses = 0
        self.evicitions = 0
        self.energy_consumption = 0
        
        self.idle_power = idle_power
        self.access_time = access_time
        self.read_write_power = read_write_power
        self.transfer_energy = transfer_energy
    
    def get_total_energy_consumption(self):
        return self.energy_consumption
    
    def set_next_cache(self, next_cache):
        self.next_cache = next_cache
        
    def get_line(self, set_index, way):
        return self.data[set_index][way]
    
    # calculate idle energy cost
    def idle(self, time):
        self.energy_consumption += self.idle_power * time
    
    # calculate access (read/write) energy cost
    def touch(self):
        self.energy_consumption += self.read_write_power * L1_ACCESS_TIME
        
    def transfer(self):
        self.energy_consumption += self.transfer_energy
        
    def size(self):
        print("cache dim:", len(self.data[0]), len(self.data))
        print("cache size:", self.capacity)
        print("num sets:", self.num_sets)
    
    def get_stats(self):
        return self.hits, self.misses, self.evicitions
    
    def evict(self, address):
        set_index = (address >> self.n_s_bits) & ((1 << self.n_s_bits) - 1)
        tag = address >> (int(log2(self.line_size)) + int(log2(self.num_sets)))
        
        # Check for hit
        empty_line = -1
        for way in range(self.assoc):
            line = self.data[set_index][way]
            if (not line.isValid()):
                empty_line = way
                continue
            
            if (line == tag):
                # the data exists in this cache, overwrite it
                
                if (line.isDirty()):
                    # if this line is dirty have to write it back to DRAM
                    self.evicitions += 1
                    self.next_cache.evict(address) # goes to DRAM, doesnt actually do anything
                    
                # remove old line
                line.remove()
                
                # put in new line
                self.data[set_index][way].valid = True
                self.data[set_index][way].tag = tag
                self.data[set_index][way].data = "data"
                self.data[set_index][way].dirty = True # this is still dirty data
                
                return True
        
        victim_way_index = random.randint(0, self.assoc - 1) if (empty_line == -1) else empty_line  # Random replacement policy

        if (self.data[set_index][victim_way_index].isDirty()):
            # have to calculate time and energy for writing back to main memory
            # have to evict this line if it exists in the next cache
            self.evicitions += 1
            self.next_cache.evict(address)
            
            # remove old line
            line.remove()
                
            # put in new line
            self.data[set_index][way].valid = True
            self.data[set_index][way].put(tag, "data") # put data in cache
            self.data[set_index][way].dirty = True # this is still dirty data
            
        else:
            # write dirty line to empty line
            self.data[set_index][victim_way_index].put(tag, "data") # put data in cache
            self.data[set_index][victim_way_index].dirty = True # this is still dirty data
            
        
        return False

    def access(self, address, op): # -> hit, evicted line
        # other_set_index = (address >> self.n_s_bits) % self.num_sets
        set_index = (address >> self.n_s_bits) & ((1 << self.n_s_bits) - 1)
        tag = address >> (int(log2(self.line_size)) + int(log2(self.num_sets)))
        
        # print(hex(address), " set_index:", set_index)

        # Check for hit
        empty_line = -1
        for way in range(self.assoc):
            line = self.data[set_index][way]
            if (not line.isValid()):
                empty_line = way
                continue
            
            if (line == tag):
                if (op == 1):
                    # writing, update dirty bit
                    line.dirty = True
                self.hits += 1
                return True
            

        # Cache miss
        self.misses += 1
        victim_way_index = random.randint(0, self.assoc - 1) if (empty_line == -1) else empty_line  # Random replacement policy
        if (self.data[set_index][victim_way_index].isDirty()):
            # have to calculate time and energy for writing back to main memory
            # have to evict this line if it exists in the next cache
            self.evicitions += 1
            self.next_cache.evict(address)
            
            
        # if evicting from l1, write to l2
        # if evicting from l2, write to dram
        
        self.data[set_index][victim_way_index].remove()
        
        hit = self.next_cache.access(address, op) # assume we can get from next memory layer (l2, main memory)
        # we wont have to write evictions that happens l2
        self.data[set_index][victim_way_index].put(tag, "data") # put data in cache
        
        return False

# DRAM simulation
class DRAM:
    def __init__(self, size, access_time, idle_power, read_write_power):
        self.size = size
        self.hits = 0
        self.misses = 0
        self.energy_consumption = 0
        self.idle_power = idle_power
        self.access_time = access_time
        self.read_write_power = read_write_power
        
    def get_stats(self):
        return self.hits, self.misses, 0
    
    def get_total_energy_consumption(self):
        return self.energy_consumption

    def access(self, address, op):
        self.hits += 1
        return True, False
    
    def idle(self, time):
        self.energy_consumption += self.idle_power * time
    
    def touch(self):
        self.energy_consumption += self.read_write_power * self.access_time
    
    def evict(self, address):
        # dont really have to do anything
        pass

    
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
L2_ASSOC = 8
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
    def __init__(self, l2_assoc):
        L2_ASSOC = l2_assoc
        L2_SETS = L2_CACHE_SIZE // (CACHE_LINE_SIZE * L2_ASSOC)
        print("\n\n**** L2 ASSOC: ", L2_ASSOC)
        self.time = 0 # p sec
        self.total_accesses = 0
        # self.total_access_time = 0
        
        self.prev_stats = {"instr_l1_hits": 0, "instr_l1_misses": 0, "data_l1_hits": 0, "data_l1_misses": 0, "l2_hits": 0, "l2_misses": 0, "mem_hits": 0, "l1_evictions": 0, "l2_evictions": 0}
        
        # capacity, line_size, assoc
        self.instr_l1 = Cache(L1_CACHE_SIZE, CACHE_LINE_SIZE, L1_ASSOC, L1_ACCESS_TIME, L1_IDLE_POWER, L1_READ_WRITE_POWER, L2_TRANSFER_ENERGY) # 32 KB
        self.data_l1 = Cache(L1_CACHE_SIZE, CACHE_LINE_SIZE, L1_ASSOC, L1_ACCESS_TIME, L1_IDLE_POWER, L1_READ_WRITE_POWER, L2_TRANSFER_ENERGY) # 32 KB
        self.l2 = Cache(L2_CACHE_SIZE, CACHE_LINE_SIZE, L2_ASSOC, L2_ACCESS_TIME, L2_IDLE_POWER, L2_READ_WRITE_POWER, DRAM_TRANSFER_ENERGY) # 256 KB
        self.dram = DRAM(DRAM_SIZE, DRAM_ACCESS_TIME, DRAM_IDLE_POWER, DRAM_READ_WRITE_POWER)
        
        self.instr_l1.set_next_cache(self.l2)
        self.data_l1.set_next_cache(self.l2)
        self.l2.set_next_cache(self.dram)
        
        # self.cs = CacheSimulator(self.instr_l1, self.mem)

    def get_avg_access_time(self):
        return self.total_access_time / self.total_accesses

    
    def update_stats(self):
        l1_hit = False
        l2_hit = False
        missed = False
        
        instr_l1_hits, instr_l1_misses, instr_l1_evictions = self.instr_l1.get_stats()
        data_l1_hits, data_l1_misses, data_l1_evictions = self.data_l1.get_stats()

        l2_hits, l2_misses, l2_evictions = self.l2.get_stats()
        memory_hits, _, _ = self.dram.get_stats()
        
        l1_hit = instr_l1_hits > self.prev_stats["instr_l1_hits"] or data_l1_hits > self.prev_stats["data_l1_hits"]
        l2_hit = l2_hits > self.prev_stats["l2_hits"]
        missed = memory_hits > self.prev_stats["mem_hits"]
        l1_evicted = instr_l1_evictions + data_l1_evictions > self.prev_stats["l1_evictions"]
        l2_evicted = l2_evictions > self.prev_stats["l2_evictions"]
        
        # update prev stats
        self.prev_stats["instr_l1_hits"] = instr_l1_hits
        self.prev_stats["instr_l1_misses"] = instr_l1_misses
        self.prev_stats["data_l1_hits"] = data_l1_hits
        self.prev_stats["data_l1_misses"] = data_l1_misses
        self.prev_stats["l2_hits"] = l2_hits
        self.prev_stats["l2_misses"] = l2_misses
        self.prev_stats["mem_hits"] = memory_hits
        self.prev_stats["l1_evictions"] = instr_l1_evictions + data_l1_evictions
        self.prev_stats["l2_evictions"] = l2_evictions
        
        assert(l2_misses == memory_hits)
        
        return l1_hit, l2_hit, missed, l1_evicted, l2_evicted
    
    def show_sim_data(self):
        data_l1_energy = self.data_l1.get_total_energy_consumption()
        instr_l1_energy = self.instr_l1.get_total_energy_consumption()
        l2_energy = self.l2.get_total_energy_consumption()
        dram_energy = self.dram.get_total_energy_consumption()
        total = data_l1_energy + instr_l1_energy + l2_energy + dram_energy
        
        print(f"\nTotal Memory Accesses: {self.total_accesses}")
        print(f"Total Memory Access Time: {self.time} pico seconds")
        print(f"Average Access Time: {self.time / self.total_accesses} pico seconds")
        
        print(f"\nTotal Energy Cost: {total} pico joules")
        print(f"> Instruction L1 Energy: {instr_l1_energy} pico joules")
        print(f"> Data L1 Energy: {data_l1_energy} pico joules")
        print(f"> L2 Energy: {l2_energy} pico joules")
        print(f"> DRAM Energy: {dram_energy} pico joules")
        
        print(f"\nL1 Hits: {self.prev_stats['instr_l1_hits'] + self.prev_stats['data_l1_hits']}")  # sum of instr and data l1 hits
        print(f"L2 Hits: {self.prev_stats['l2_hits']}")
        print(f"Cache Misses: {self.prev_stats['mem_hits']}")
        
        # print(f"Evictions: {self.prev_stats['evictions']}")
        print(f"L1 Evictions: {self.prev_stats['l1_evictions']}")
        print(f"L2 Evictions: {self.prev_stats['l2_evictions']}")
        
        
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
    
    # actually runs the interactions of the cache
    def execute(self, address, op, value):
        if (op == 0):
            # Memory read
            self.data_l1.access(address, op)
        elif (op == 1):
            # Memory write
            self.data_l1.access(address, op)
        elif (op == 2):
            # Instruction fetch
            self.instr_l1.access(address, op)
        elif (op == 3):
            # Ignore
            self.idle()
        elif (op == 4):
            # Flush Cache
            self.flush_cache()
            
        pass
    
    # ED: "copy of data DRAM -> L2 and L2 -> L1 on misses do not take extra time or extra active energy for the writes - this is included in penalty energy."
    
    def step_other(self, op):
                # for each action, check current state with previous stats to see what happened
        l1_hit, l2_hit, missed, l1_evicted, l2_evicted = self.update_stats()
        
        time_passed = 0
        
        assert(not (l1_hit and l2_hit))
        assert(not (l1_hit and missed))
        assert(not (l2_hit and missed))
        
        # Ignore instruction (idle)
        if (op == 3):
            time_passed = 0.5  # nsec
            # energy_consumed = L1_IDLE_POWER * time_passed # l1 idle energy
            # energy_consumed += L2_IDLE_POWER * time_passed # l2 idle energy
            # energy_consumed += DRAM_IDLE_POWER * time_passed # dram idle energy

        
        l1_active = self.data_l1
        l1_passive = self.instr_l1
        if (op == 2): # instruction fetch
            l1_active = self.instr_l1
            l1_passive = self.data_l1
                
        elif (l1_hit):
            time_passed = L1_ACCESS_TIME
            
            # check l1
            l1_active.touch()
            l1_passive.idle(L1_ACCESS_TIME)
            self.l2.idle(L1_ACCESS_TIME)
            self.dram.idle(L1_ACCESS_TIME)
            
        elif (l2_hit):
            time_passed = L1_ACCESS_TIME + L2_ACCESS_TIME 
            
            # check l2
            self.l2.touch()
            l1_active.idle(L2_ACCESS_TIME)
            l1_passive.idle(L2_ACCESS_TIME)
            self.dram.idle(L2_ACCESS_TIME)
            
            # transfer to L1
            l1_active.transfer()
            
            # now actually read or write L1
            l1_active.touch()
            l1_passive.idle(L1_ACCESS_TIME)
            self.l2.idle(L1_ACCESS_TIME)
            self.dram.idle(L1_ACCESS_TIME)

        else:
            # miss to l1 and l2
            time_passed = L1_ACCESS_TIME + DRAM_ACCESS_TIME
            
            # read from main memory (50 nsec)
            self.dram.touch()
            l1_active.idle(DRAM_ACCESS_TIME)
            l1_passive.idle(DRAM_ACCESS_TIME)
            self.l2.idle(DRAM_ACCESS_TIME)
            
            # transfer to L2
            self.l2.transfer()
            # transfer to L1
            l1_active.transfer()
                        
            # now actually read or write L1
            l1_active.touch()
            l1_passive.idle(L1_ACCESS_TIME)
            self.l2.idle(L1_ACCESS_TIME)
            self.dram.idle(L1_ACCESS_TIME)
            
        if (l1_evicted):
            time_passed += L2_ACCESS_TIME
            self.l2.touch() # clear l2 entry

            self.dram.idle(L2_ACCESS_TIME) # write to dram
            l1_active.idle(L2_ACCESS_TIME)
            l1_passive.idle(L2_ACCESS_TIME)
            
        if (l2_evicted):
            time_passed += DRAM_ACCESS_TIME
            self.dram.touch() # write to dram

            self.l2.idle(DRAM_ACCESS_TIME) 
            l1_active.idle(DRAM_ACCESS_TIME)
            l1_passive.idle(DRAM_ACCESS_TIME)

        self.total_accesses += 1
        self.time += time_passed
        
        pass
                
    def step(self, op):
        # for each action, check current state with previous stats to see what happened
        l1_hit, l2_hit, missed, l1_evicted, l2_evicted = self.update_stats()
        
        time_passed = 0
        
        assert(not (l1_hit and l2_hit))
        assert(not (l1_hit and missed))
        assert(not (l2_hit and missed))
        
        # Ignore instruction (idle)
        if (op == 3):
            time_passed = 0.5  # nsec
            energy_consumed = L1_IDLE_POWER * time_passed # l1 idle energy
            energy_consumed += L2_IDLE_POWER * time_passed # l2 idle energy
            energy_consumed += DRAM_IDLE_POWER * time_passed # dram idle energy
        
        l1_active = self.data_l1
        l1_passive = self.instr_l1
        if (op == 2): # instruction fetch
            l1_active = self.instr_l1
            l1_passive = self.data_l1
                
        elif (l1_hit):
            time_passed = L1_ACCESS_TIME
            
            # check l1
            l1_active.touch()
            l1_passive.idle(L1_ACCESS_TIME)
            self.l2.idle(L1_ACCESS_TIME)
            self.dram.idle(L1_ACCESS_TIME)
            
        elif (l2_hit):
            time_passed = L1_ACCESS_TIME + L2_ACCESS_TIME + L1_ACCESS_TIME + L1_ACCESS_TIME
            
            # check l1
            l1_active.touch()
            l1_passive.idle(L1_ACCESS_TIME)
            self.l2.idle(L1_ACCESS_TIME)
            self.dram.idle(L1_ACCESS_TIME)
            
            # check l2
            self.l2.touch()
            l1_active.idle(L2_ACCESS_TIME)
            l1_passive.idle(L2_ACCESS_TIME)
            self.dram.idle(L2_ACCESS_TIME)
            
            # transfer to L1
            l1_active.transfer()
            
            # write to L1
            l1_active.touch()
            l1_passive.idle(L1_ACCESS_TIME)
            self.l2.idle(L1_ACCESS_TIME)
            self.dram.idle(L1_ACCESS_TIME)
                        
            # now actually read or write L1
            l1_active.touch()
            l1_passive.idle(L1_ACCESS_TIME)
            self.l2.idle(L1_ACCESS_TIME)
            self.dram.idle(L1_ACCESS_TIME)

        else:
            # miss to l1 and l2
            time_passed = L1_ACCESS_TIME + L2_ACCESS_TIME + DRAM_ACCESS_TIME + L2_ACCESS_TIME + L1_ACCESS_TIME
            
            # check l1
            l1_active.touch()
            l1_passive.idle(L1_ACCESS_TIME)
            self.l2.idle(L1_ACCESS_TIME)
            self.dram.idle(L1_ACCESS_TIME)
            
            # check l2
            self.l2.touch()
            l1_active.idle(L2_ACCESS_TIME)
            l1_passive.idle(L2_ACCESS_TIME)
            self.dram.idle(L2_ACCESS_TIME)
            
            # read from main memory (50 nsec)
            self.dram.touch()
            l1_active.idle(DRAM_ACCESS_TIME)
            l1_passive.idle(DRAM_ACCESS_TIME)
            self.l2.idle(DRAM_ACCESS_TIME)
            
            # transfer to L2
            self.l2.transfer()
            # transfer to L1
            l1_active.transfer()
            
            # write to L2 and L1: this happens in parallel
            l1_active.touch()
            l1_active.idle(L2_ACCESS_TIME - L1_ACCESS_TIME)
            self.l2.touch()
            l1_passive.idle(L2_ACCESS_TIME)
            self.dram.idle(L2_ACCESS_TIME)
                        
            # now actually read or write L1
            l1_active.touch()
            l1_passive.idle(L1_ACCESS_TIME)
            self.l2.idle(L1_ACCESS_TIME)
            self.dram.idle(L1_ACCESS_TIME)
            
        # if (evicted):
        #     time_passed += DRAM_ACCESS_TIME
        #     self.dram.touch() # write to dram
        #     l1_active.touch() # clear l1 entry
        #     self.l2.touch() # clear l2 entry

        #     l1_active.idle(L1_ACCESS_TIME - DRAM_ACCESS_TIME)
        #     l1_passive.idle(DRAM_ACCESS_TIME)
        #     self.l2.idle(L2_ACCESS_TIME - DRAM_ACCESS_TIME)

        self.total_accesses += 1
        self.time += time_passed
        
        pass
    
    
    
def run_all_traces(L2_ASSOC):
    for trace in os.listdir("Traces/Spec_Benchmark"):
        run_trace(trace, L2_ASSOC)
        
def run_trace(trace, L2_ASSOC):
    if (not trace.endswith(".din")):
        return
        
    simulator = SIM(L2_ASSOC)
    file_path = os.path.join("Traces/Spec_Benchmark", trace)
    parsed_data = parse_trace_file(file_path)

    print(f"\n\nRunning trace: {trace}")
    for op, address, value in parsed_data:
        # print(f"OP: {op}, Address: {address}, Value: {value}")
        assert(op != 4)
        simulator.execute(address, op, value)
        simulator.step_other(op)

        # break
        
    simulator.show_sim_data()
    

def main():
    assoc_values = [2, 4, 8]
    for assoc in assoc_values:
        # print(f"\n\nRunning simulation with {assoc} associativity")
        L2_ASSOC = assoc
        # run_trace("custom.din", L2_ASSOC)
        run_all_traces(L2_ASSOC)
    
   

if __name__ == "__main__":
    main()
