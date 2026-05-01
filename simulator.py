import collections
from models import Task, CPU

class Simulator:
    def __init__(self, tasks, cpu, algorithm="round_robin", time_quantum=2, is_baseline=False):
        # Clone tasks to avoid modifying original state across runs
        self.all_tasks = sorted([t.clone() for t in tasks], key=lambda x: x.arrival_time)
        self.ready_queue = collections.deque()
        self.completed_tasks = []
        self.cpu = cpu
        self.algorithm = algorithm
        self.time_quantum = time_quantum
        self.is_baseline = is_baseline
        self.current_time = 0
        
        # Performance history for plotting
        self.history = {
            "time": [],
            "cpu_temp": [],
            "cpu_freq": [],
            "cpu_power": [],
            "cumulative_energy": [],
            "queue_length": [],
            "active_task": []
        }

    def run(self):
        task_idx = 0
        current_task = None
        quantum_left = self.time_quantum

        while task_idx < len(self.all_tasks) or self.ready_queue or current_task:
            # 1. Add tasks that have arrived
            while task_idx < len(self.all_tasks) and self.all_tasks[task_idx].arrival_time <= self.current_time:
                self.ready_queue.append(self.all_tasks[task_idx])
                task_idx += 1

            # 2. Power & Thermal Management (DVFS Logic)
            self.apply_power_policy()

            # 3. Scheduling Logic
            if not current_task and self.ready_queue:
                current_task = self.ready_queue.popleft()
                quantum_left = self.time_quantum
                if current_task.start_time is None:
                    current_task.start_time = self.current_time
                self.cpu.is_busy = True
            
            # 4. Execute Task for 1 unit of time
            if current_task:
                # Work done depends on CPU frequency
                # Normalize 2.4GHz as 1.0 work unit per time unit
                work_done = self.cpu.frequency / 2.4
                current_task.remaining_time -= work_done
                quantum_left -= 1
                
                if current_task.remaining_time <= 0:
                    current_task.completion_time = self.current_time + 1
                    current_task.turnaround_time = current_task.completion_time - current_task.arrival_time
                    current_task.waiting_time = current_task.turnaround_time - current_task.burst_time
                    self.completed_tasks.append(current_task)
                    current_task = None
                    self.cpu.is_busy = False
                elif self.algorithm == "round_robin" and quantum_left <= 0:
                    self.ready_queue.append(current_task)
                    current_task = None
                    self.cpu.is_busy = False
            else:
                self.cpu.is_busy = False

            # 5. Update CPU State
            self.cpu.update_thermal_state(delta_time=1.0)
            
            # Record History
            self.history["time"].append(self.current_time)
            self.history["cpu_temp"].append(self.cpu.temperature)
            self.history["cpu_freq"].append(self.cpu.frequency)
            self.history["cpu_power"].append(self.cpu.get_power())
            self.history["cumulative_energy"].append(self.cpu.total_energy_consumed)
            self.history["queue_length"].append(len(self.ready_queue))
            self.history["active_task"].append(current_task.id if current_task else None)

            self.current_time += 1
            
            # Safety break
            if self.current_time > 10000:
                break

        return self.history

    def apply_power_policy(self):
        """
        Custom Power-Aware Policy implementation:
        
        1. Baseline Mode: 
           Always stay at Max Frequency/Voltage.
        
        2. Thermal Throttling (Safety First):
           If temperature exceeds 75°C, immediately drop to lowest frequency/voltage.
        
        3. Load-Based DVFS (Efficiency):
           - High Workload (>4 tasks in queue): Max Frequency (2.4 GHz).
           - Medium Workload (3-4 tasks): High Frequency (2.0 GHz).
           - Low Workload (1-2 tasks): Medium Frequency (1.6 GHz).
           - Idle (0 tasks): Power Save (1.2 GHz).
        """
        # Baseline: No dynamic adjustments
        if self.is_baseline:
            self.cpu.set_dvfs_state(len(self.cpu.dvfs_states) - 1)
            return

        # Thermal Throttling
        if self.cpu.temperature > 75:
            self.cpu.set_dvfs_state(0)
            return

        # DVFS based on ready queue length
        q_len = len(self.ready_queue)
        if q_len > 4:
            self.cpu.set_dvfs_state(4)
        elif q_len > 2:
            self.cpu.set_dvfs_state(3)
        elif q_len > 0:
            self.cpu.set_dvfs_state(2)
        else:
            self.cpu.set_dvfs_state(1)

# Feature branch: Finalizing analytical models.
