import random
from collections import deque

# Constants for the simulation
COMPUTE_TICKS = 5  # CPU ticks required for a COMPUTE instruction
INPUT_TICKS = 1 # CPU ticks required for a INPUT instruction
OUTPUT_TICKS = 1 # CPU ticks required for a OUTPUT instruction
quantum = 0 

# Process states
READY = "READY"
RUNNING = "RUNNING"
BLOCKED = "BLOCKED"
COMPLETED = "COMPLETED"  # New state for completed processes

scmenu = {"stop": "Stop the simulation and display summary statistics", "show jobs": "Display all active processes with the status of each process", "show queues": "Display the contents of each queue (Ready Queue, Blocked Queue)", "show memory": "Display a map of memory showing starting location of each job", "tick n": "Run the simulation for a specified number of ticks", "admit progname" : "Admit the specified program as a job", "interrupt n" : "Any process that is waiting on the event will be moved from the Blocked Queue into the Ready Queue."}
stats = {}
processes = deque()

def print_menu(menu): # prints dictionary
        for key, value in menu.items(): print(f"{key}: {value}")

def show_inactive_jobs(): # Display all active processes with the status of each process
    print_menu(dict(processes))

class Process: #Creates process

    def __init__(self, pid, instructions, mem_u):
        self.pid = pid
        self.instructions = deque(instructions)
        self.status = READY
        self.program_counter = 0 
        self.cpu_ticks = 0 #total time for each completed process
        self.mem_u = mem_u
        self.remcticks = COMPUTE_TICKS
        self.remiticks = INPUT_TICKS
        self.remoticks = OUTPUT_TICKS
        self.event_waiting = 0
        self.size = len(self.instructions)

    def __str__(self):
        return f"Process ID {self.pid}, Instructions={self.instructions}, Status={self.status}, PC={self.program_counter}, CPU ticks={self.cpu_ticks}, Event Waiting={self.event_waiting}, Process Size={self.size}"

class MemoryManager: # Manage memory
    
    def __init__(self, os_memory, user_memory, allocation_mode):
        self.os_memory = os_memory
        self.user_memory = user_memory
        self.allocation_mode = allocation_mode
        self.memory = [None] * user_memory
        self.last_alloc_position = 0

    # FUNCTION TO ALLOCATE MEMORY BASED ON ALLOCATION MODE:
    def allocate(self, pid, size):
        if size <= self.user_memory:
            if "FF" in self.allocation_mode or "First Fit" in self.allocation_mode:
                try:
                    for i in range(self.user_memory - size + 1):
                        if all(slot is None for slot in self.memory[i:i + size]):
                            for j in range(size):
                                self.memory[i + j] = pid
                            #print(f"Job {pid} allocated at position {i} using First Fit")
                            return True
                #print(f"No suitable block found for Job {pid} using First Fit")
                except IndexError:
                        print(f"IndexError: Process {pid} could not be allocated memory.")
                        return False
            elif "BF" in self.allocation_mode or "Best Fit" in self.allocation_mode:
                pos_blocks = []  # List to store tuples (start_index, block_size)
                i = 0
                try:
                    while i < self.user_memory:
                        if self.memory[i] is None:  # Found a free spot
                            start = i
                            # Find the end of the free block
                            while i < self.user_memory and self.memory[i] is None:
                                i += 1
                            block_size = i - start  # Calculate the size of the block
                            # Add block to pos_blocks if it's large enough
                            if block_size >= size:
                                pos_blocks.append((start, block_size))
                        else:
                            i += 1  # Move to the next position if this slot is occupied
                    if pos_blocks:  # If we have found at least one suitable block
                        # Sort the list of potential blocks by block size (smallest first)
                        pos_blocks.sort(key=lambda x: x[1])
                        # The best block is the first one in the sorted list
                        best_start, best_size = pos_blocks[0]  
                        try:
                            # Allocate memory to the selected block
                            for j in range(size):
                                # Check if we are trying to access out of bounds
                                if best_start + j >= self.user_memory:
                                    raise IndexError(f"Memory allocation failed: Process {pid} cannot be allocated to the block starting at {best_start}. Out of bounds.")
                                self.memory[best_start + j] = pid
                            #print(f"Job {pid} allocated at position {best_start} using Best Fit")
                            return True
                        except IndexError as e:
                            print(e)
                            return False
                    else:
                        # No suitable block was found
                        #print(f"No suitable block found for Job {pid} using Best Fit")
                        print(f"IndexError: Process {pid} could not be allocated memory.")
                        return False
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")
                    return False
            elif "NF" in self.allocation_mode or "Next Fit" in self.allocation_mode:
                start = self.last_alloc_position
                while True:
                    try:
                        if all(slot is None for slot in self.memory[start:start + size]):
                            for j in range(size):
                                self.memory[start + j] = pid
                            self.last_alloc_position = (start + size) % self.user_memory
                            #print(f"Job {pid} allocated at position {start} using Next Fit")
                            return True
                        start = (start + 1) % self.user_memory
                    except IndexError:
                        print(f"IndexError: Process {pid} could not be allocated memory.")
                        return False
                    if start == self.last_alloc_position:
                        break
            else:
                return False
            
    def deallocate(self, pid):
        for id in range(len(self.memory)):
            if self.memory[id] == pid:
                self.memory[id] = None

    def show_memory(self): # Display a map of memory showing starting location of each job
        print(f"OS Memory: {self.os_memory}, User Memory: {self.user_memory}")
        print("Memory:", self.memory)

class Scheduler:

    def __init__(self):
        self.ready_queue = deque()
        self.blocked_queue = deque()
        self.completed_processes = []  # Store completed processes
        self.current_process = None
        m = MemoryManager

    def admit_process(self, process): #WORKING
        if not(len(process.instructions) == 0):
            self.ready_queue.append(process)
            print(f"Process {process.pid} admitted to the ready queue.")

    def tick(self): 
        state = False
        # Schedule a new process if there's one in the ready queue
        if not self.current_process and self.ready_queue:
            self.current_process = self.ready_queue.popleft()
            self.current_process.status = RUNNING
            print(f"Process {self.current_process.pid} is now running.")
            if not (len(self.current_process.instructions) == 0):
                instruction = self.current_process.instructions.popleft()
                self.current_process.program_counter += 1
                # Preempt the current process if needed (after quantum/ Timeout)
                if instruction == "COMPUTE":
                    print(f"Ticks: {self.current_process.remcticks}")
                    if(self.current_process.remcticks > quantum):
                        self.current_process.remcticks -= quantum
                        self.current_process.instructions.appendleft(instruction)
                        self.current_process.status = READY 
                        self.ready_queue.append(self.current_process)
                    else:
                        self.current_process.remcticks = 5
                        if not(len(self.current_process.instructions) == 0):
                            print(f"Ticks: {self.current_process.instructions}")
                            self.ready_queue.append(self.current_process)
                elif instruction == "INPUT":
                    self.current_process.status = BLOCKED
                    print(f"Process {self.current_process.pid} is blocked.")
                    self.current_process.event_waiting = 1  # Waiting for INPUT event
                    self.current_process.instructions.appendleft(instruction)
                    self.blocked_queue.append(self.current_process)
                elif instruction == "OUTPUT":
                    self.current_process.status = BLOCKED
                    print(f"Process {self.current_process.pid} is blocked.")
                    self.current_process.event_waiting = 2  # Waiting for OUTPUT event
                    self.current_process.instructions.appendleft(instruction)
                    self.blocked_queue.append(self.current_process)
    
                self.current_process.cpu_ticks += 1     

            if (len(self.current_process.instructions) == 0):
                self.current_process.status = COMPLETED
                self.completed_processes.append(self.current_process)
                state = True
            
        return state

    def handle_interrupt(self): #An interrupt event that moves any process that is waiting on the event from the Blocked Queue into the Ready Queue 
        state = False
        # Schedule a new process if there's one in the ready queue
        if not self.current_process and self.ready_queue:
            self.current_process = self.ready_queue.popleft()
            self.current_process.status = RUNNING
            print(f"Process {self.current_process.pid} is now running.")
            if not (len(self.current_process.instructions) == 0):
                instruction = self.current_process.instructions.popleft()
                self.current_process.program_counter += 1
                # Preempt the current process if needed (after quantum/ Timeout)
                if instruction == "INPUT":
                    print(f"Ticks: {self.current_process.remiticks}")
                    if(self.current_process.remiticks > quantum):
                        self.current_process.remiticks -= quantum
                        self.current_process.instructions.appendleft(instruction)
                        self.current_process.status = READY 
                        self.ready_queue.append(self.current_process)
                    else:
                        self.current_process.remiticks = 1
                        if not(len(self.current_process.instructions) == 0):
                            print(f"Ticks: {self.current_process.instructions}")
                            self.ready_queue.append(self.current_process) 

                elif instruction == "OUTPUT":
                    print(f"Ticks: {self.current_process.remoticks}")
                    if(self.current_process.remoticks > quantum):
                        self.current_process.remoticks -= quantum
                        self.current_process.instructions.appendleft(instruction)
                        self.current_process.status = READY 
                        self.ready_queue.append(self.current_process)
                    else:
                        self.current_process.remoticks = 1
                        if not(len(self.current_process.instructions) == 0):
                            print(f"Ticks: {self.current_process.instructions}")
                            self.ready_queue.append(self.current_process)
    
                self.current_process.cpu_ticks += 1     

            if (len(self.current_process.instructions) == 0):
                self.current_process.status = COMPLETED
                self.completed_processes.append(self.current_process)
                state = True
            
        return state         

    def show_queues(self):
        print("Ready Queue:", [[p.pid, len(p.instructions), p.status, p.program_counter, p.cpu_ticks, p.event_waiting] for p in self.ready_queue])
        print("Blocked Queue:", [[p.pid, len(p.instructions), p.status, p.program_counter, p.cpu_ticks, p.event_waiting] for p in self.blocked_queue])
        print("Completed Queue:", [[p.pid, len(p.instructions), p.status, p.program_counter, p.cpu_ticks, p.event_waiting] for p in self.completed_processes])

    def show_jobs(self):
        pass

    def all_processes_complete(self):
        # Check if all queues are empty, no running process, and no blocked process
        return not self.ready_queue and not self.blocked_queue and self.current_process is None

class BasicOS:

    def __init__(self, s, m):
        self.s = s
        self.m = m

    def show_queues(self):
        self.s.show_queues()
    def show_memory(self):
        self.m.show_memory()
    def admit_process(self): #Admit the specified program as a job
        prog_ID = input("Enter job ID (eg. job 1) to admit specific program as a job or enter 'all' to admit all programs as jobs: ")
        for p in processes:
            if prog_ID == "all":
                if (p[1] not in self.s.ready_queue):
                    if self.m.allocate(p[1].pid, p[1].size):
                        self.s.admit_process(p[1])
            else:
                if p[0] == prog_ID: 
                    if self.m.allocate(p[1].pid, p[1].size):
                        self.s.admit_process(p[1])
    def show_jobs(self):
        self.s.show_jobs()
    
    def interrupt(self, event_number):
        if not(len(self.s.blocked_queue) == 0):
            for process in list(self.s.blocked_queue):
                if process.event_waiting == event_number:
                    process.status = READY
                    process.event_waiting = 0
                    self.s.ready_queue.append(process)
                    self.s.blocked_queue.remove(process)
                    print(f"Process {process.pid} moved to ready queue due to interrupt {event_number}.")
                    completed = self.s.handle_interrupt()
                    if not completed:
                        self.s.current_process = None  # Remove the completed process
                    else:
                        self.m.deallocate(self.s.current_process.pid)
                        print(f"Process {self.s.current_process.pid} has completed and memory deallocated.")
                        self.s.current_process = None  # Remove the completed process
                        if self.s.all_processes_complete():
                            print("All processes are completed.")
                            break

    def tick(self, n): # Run the simulation for a specified number of ticks
        for _ in range(n):
            completed = self.s.tick()
            # If the process has no more instructions, mark it as completed
            if not completed:
                self.s.current_process = None  # Remove the completed process
            else:
                self.m.deallocate(self.s.current_process.pid)
                print(f"Process {self.s.current_process.pid} has completed and memory deallocated.")
                self.s.current_process = None  # Remove the completed process
                if self.s.all_processes_complete():
                    print("All processes are completed.")
                    break
        

    def basicOS(self):  
        print("\nSIMULATOR COMMANDS\n") 
        print_menu(scmenu)
        sc = input("\nEnter a simulator command: ")

        match sc:
            case "stop":
                self.basicOS()
            case "show jobs":
                show_inactive_jobs()
                self.basicOS()
            case "show queues":
                self.show_queues()
                self.basicOS()
            case "show memory":
                self.show_memory()
                self.basicOS()
            case "admit progname":
                self.admit_process()
                self.basicOS()
        if "interrupt" in sc:
            n = sc.split(" ")[1]
            self.interrupt(int(n))
            self.basicOS()
        if "tick" in sc:
            n = sc.split(" ")[1]
            self.tick(int(n))
            self.basicOS()
        else:
            print("Invalid simulator command")
            self.basicOS()
    
        
if __name__ == "__main__":
    print("SETTINGS\n")
    memory_s = input("Enter the amount of RAM reserved for the OS (eg: 64): ")
    memory_u = input("Enter the amount of memory available for user processes (eg: 128): ")
    degreem_n = input("Enter the degree of multiprogramming (eg: 5): ")
    context_x = input("Enter the number of ticks it takes the processor to switch from one process to the next: ")
    quantum = int(context_x)
    allocation_mode = input("Memory Allocation Strategies:\nFirst Fit (FF): Place the job in the first available memory locations.\nBest Fit (BF): Place the job in the smallest hole that can accommodate it.\nNext Fit (NF). Place the job in the first available hole after the point where the last allocation was made.\nEnter the memory allocation strategy to be used: ")
    
    print("\n")
    inst_id = 0
    instructions = {}
    # Open the files in read mode 
    for n in range(int(degreem_n)):
        filename = input("Enter the name of the text file (eg: process.txt): ")
        file = open(filename, "r") 
        inst = file.read().strip()
        instructions[inst_id] = inst.split("\n")
        inst_id += 1
        file.close()
    print("Instructions for " + degreem_n + " processes have been loaded")

    for key, value in instructions.items(): # load processes
        p = Process(key, value, int(memory_u))
        processes.append(("job "+str(p.pid), p ))
    print(degreem_n + " processes have been loaded")

    scheduler = Scheduler()
    memorymanager = MemoryManager(int(memory_s), int(memory_u), allocation_mode)
    basicOS = BasicOS(scheduler, memorymanager)
    basicOS.basicOS()

    # def stop(): # Stop the simulation and display summary statistics
    #     print("SUMMARY STATISTICS")
    #     print("The amount of RAM reserved for the OS: "+memory_s)
    #     print("The amount of memory available for user processes: "+memory_u)
    #     print("The degree of multiprogramming: "+degreem_n)
    #     print("The number of ticks it takes the processor to switch from one process to the next: "+context_x)
    #     print("Memory Allocation Strategie: "+allocation_mode)
    #     print("Number of jobs completed: "+scheduler.completed_processes)


    
       
    