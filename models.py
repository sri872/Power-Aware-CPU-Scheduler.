import math

class Task:
    def __init__(self, task_id, arrival_time, burst_time, priority=0):
        self.id = task_id
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.priority = priority
        self.start_time = None
        self.completion_time = None
        self.waiting_time = 0
        self.turnaround_time = 0

    def clone(self):
        """Returns a fresh copy of the task with reset state."""
        return Task(self.id, self.arrival_time, self.burst_time, self.priority)

    def __repr__(self):
        return f"Task(ID={self.id}, Arrival={self.arrival_time}, Remaining={self.remaining_time})"

class CPU:
    def __init__(self, ambient_temp=25.0):
        # Frequency in GHz, Voltage in Volts
        # Common DVFS states (Freq, Voltage)
        self.dvfs_states = [
            (0.8, 0.9),
            (1.2, 1.0),
            (1.6, 1.1),
            (2.0, 1.2),
            (2.4, 1.3)
        ]
        self.current_state_idx = len(self.dvfs_states) - 1  # Start at max performance
        self.frequency, self.voltage = self.dvfs_states[self.current_state_idx]
        
        self.temperature = ambient_temp
        self.ambient_temp = ambient_temp
        self.total_energy_consumed = 0.0
        
        # Thermal constants (simplified)
        self.heat_coeff = 0.05   # How fast it heats up per unit of power
        self.cooling_coeff = 0.02 # How fast it cools down towards ambient
        
        self.is_busy = False

    def get_power(self):
        """
        Calculates power consumption based on P = C * V^2 * f.
        C (Capacitance) is assumed as 1.0.
        Idle power is 10% of the active power at the lowest voltage state.
        """
        if not self.is_busy:
            return 0.1 * (self.dvfs_states[0][1] ** 2) * self.dvfs_states[0][0]
        return (self.voltage ** 2) * self.frequency

    def update_thermal_state(self, delta_time=1.0):
        """
        Updates CPU temperature using Newton's Law of Cooling.
        dT/dt = (Heat Generated) - (Heat Dissipated)
        Heating is proportional to power consumption.
        Cooling is proportional to the difference between current and ambient temp.
        """
        power = self.get_power()
        
        heating = self.heat_coeff * power
        cooling = self.cooling_coeff * (self.temperature - self.ambient_temp)
        
        self.temperature += (heating - cooling) * delta_time
        self.total_energy_consumed += power * delta_time

    def set_dvfs_state(self, state_idx):
        if 0 <= state_idx < len(self.dvfs_states):
            self.current_state_idx = state_idx
            self.frequency, self.voltage = self.dvfs_states[state_idx]

    def __repr__(self):
        return f"CPU(Freq={self.frequency}GHz, Temp={self.temperature:.2f}C, Power={self.get_power():.2f}W)"
