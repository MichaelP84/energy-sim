# How to Run Code

### To run our simulator run the run.sh file, make sure its permissions are set to executable (chmod u+x run.sh) and sun ./run.sh
### Our simulator will run the 15 traces 3 times, once for each L2 Associativity (2, 4, 8)

# Output format of our simulator

## One trace at one assoc:

## """
## **** L2 ASSOC:  2


## Running trace: 048.ora.din                               (the trace being run)

## Total Memory Accesses: 1000002                           
## Total Memory Access Time: 101370500.0 pico seconds
## Average Access Time: 101.37029725940548 pico seconds

## Total Energy Cost: 317062395.0 pico joules
## > Instruction L1 Energy: 50685250.0 pico joules
## > Data L1 Energy: 100743265.0 pico joules
## > L2 Energy: 81017480.0 pico joules
## > DRAM Energy: 84616400.0 pico joules

## L1 Hits: 999885                                          (combined data and instruction l1 hits)
## L2 Hits: 72
## Cache Misses: 45
## L1 Evictions: 0                                          (evictions of dirty lines from L1 to L2)
## L2 Evictions: 0                                          (evictions of dirty lines from L2 to DRAM)

## .
## .
## .
