# ⚡ Advanced Power-Aware CPU Scheduler

An interactive Operating Systems simulation that demonstrates **Dynamic Voltage and Frequency Scaling (DVFS)** and **Thermal-Aware Scheduling**. This project compares a standard "Performance-First" scheduler against an "Energy-Efficient" scheduler to visualize power savings and thermal stability.

## 🚀 Key Features
- **Real-time Telemetry**: Track Temperature, Frequency, and Power consumption simultaneously.
- **Algorithm Comparison**: Side-by-side analysis of Baseline (Fixed Freq) vs. Power-Aware (DVFS).
- **Thermal Safety**: Automatic frequency throttling when the CPU crosses the 75°C threshold.
- **Performance Metrics**: Calculates Energy Savings (%), Thermal Reduction (°C), and Latency Trade-offs.

---

## 🌍 Real-World Architecture
This simulator maps directly to how modern smartphones (Android/iOS) and laptops manage battery life and heat.

| Simulator Component | Real-World Equivalent | Function |
| :--- | :--- | :--- |
| `apply_power_policy()` | **CPU Governor** | The kernel logic (like *Schedutil*) that decides CPU speed. |
| `cpu.set_dvfs_state()` | **PMIC & VRM** | The hardware that physically changes Voltage and Clock speed. |
| `Ambient Temp Slider` | **Thermal Diodes** | Physical sensors in the silicon that report heat to the OS. |
| `Task Arrival` | **Hardware Interrupts** | Signals from the screen, network, or keyboard to the Kernel. |
| `Thermal Limit (75°C)` | **OS Throttling** | Software protection to keep devices comfortable to hold. |

---

## 🛠️ Technology Stack
- **Language**: Python 3.x
- **Framework**: Streamlit (Dashboard)
- **Visualization**: Plotly (Interactive Graphs)
- **Data Analysis**: Pandas

---

## 🏃 How to Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Launch the application:
   ```bash
   streamlit run app.py
   ```

## 📊 Mathematical Models
The project uses the CMOS power equation:
$$P \propto V^2 \times f$$
Where:
- **P**: Power Consumption
- **V**: Voltage
- **f**: Operating Frequency

Thermal updates follow **Newton's Law of Cooling**, where the rate of temperature change is proportional to the power generated minus the heat dissipated to the ambient environment.
