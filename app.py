import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from models import Task, CPU
from simulator import Simulator
import random

# Page Config
st.set_page_config(page_title="Power-Aware CPU Scheduler", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for premium look
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    h1, h2, h3 {
        color: #00d4ff;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Power-Aware CPU Scheduling Simulator")
st.markdown("Optimize energy consumption and thermal safety using DVFS and Thermal-Aware scheduling.")

# Sidebar Configuration
st.sidebar.header("🛠️ Simulation Parameters")
num_tasks = st.sidebar.slider("Number of Tasks", 5, 50, 15)
ambient_temp = st.sidebar.slider("Ambient Temperature (°C)", 10.0, 45.0, 25.0)
time_quantum = st.sidebar.slider("RR Time Quantum", 1, 10, 2)
algo_type = st.sidebar.selectbox("Scheduling Policy", ["Baseline (No DVFS)", "Power-Aware (DVFS + Thermal)"])

# Task Generation
def generate_tasks(n):
    tasks = []
    for i in range(n):
        arrival = random.randint(0, 20)
        burst = random.randint(5, 30)
        tasks.append(Task(f"T{i+1}", arrival, burst))
    return tasks

if 'tasks' not in st.session_state:
    st.session_state.tasks = generate_tasks(num_tasks)

if st.sidebar.button("🔄 Regenerate Tasks"):
    st.session_state.tasks = generate_tasks(num_tasks)
    st.rerun()

# Run Simulation
cpu = CPU(ambient_temp=ambient_temp)
if algo_type == "Baseline (No DVFS)":
    # Mock a fixed max frequency
    cpu.set_dvfs_state(len(cpu.dvfs_states)-1)
    # Override apply_power_policy in a subclass or just handle it here
    class BaselineSimulator(Simulator):
        def apply_power_policy(self):
            self.cpu.set_dvfs_state(len(self.cpu.dvfs_states)-1)
    sim = BaselineSimulator(st.session_state.tasks, cpu, time_quantum=time_quantum)
else:
    sim = Simulator(st.session_state.tasks, cpu, time_quantum=time_quantum)

history = sim.run()

# Metrics
col1, col2, col3, col4 = st.columns(4)
total_energy = cpu.total_energy_consumed
avg_wait = sum(t.waiting_time for t in sim.completed_tasks) / len(sim.completed_tasks) if sim.completed_tasks else 0
max_temp = max(history["cpu_temp"])
throughput = len(sim.completed_tasks) / sim.current_time if sim.current_time > 0 else 0

col1.metric("Total Energy", f"{total_energy:.2f} J", delta=None)
col2.metric("Avg Waiting Time", f"{avg_wait:.2f} units", delta=None, delta_color="inverse")
col3.metric("Peak Temperature", f"{max_temp:.2f} °C", delta=None, delta_color="inverse")
col4.metric("Throughput", f"{throughput:.2f} tasks/t", delta=None)

# Visualizations
st.subheader("📈 Real-time CPU Telemetry")
df_hist = pd.DataFrame(history)

fig = go.Figure()
fig.add_trace(go.Scatter(x=df_hist["time"], y=df_hist["cpu_temp"], name="Temperature (°C)", line=dict(color="#ff4b4b", width=2)))
fig.add_trace(go.Scatter(x=df_hist["time"], y=df_hist["cpu_freq"] * 20, name="Freq (GHz x 20)", line=dict(color="#00d4ff", width=2, dash='dot')))
fig.add_trace(go.Scatter(x=df_hist["time"], y=df_hist["cpu_power"] * 10, name="Power (W x 10)", line=dict(color="#00ff00", width=2)))

fig.update_layout(template="plotly_dark", hovermode="x unified", height=500, margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig, use_container_width=True)

# Gantt Chart
st.subheader("🗓️ Task Execution Timeline")
gantt_data = []
for t in sim.completed_tasks:
    gantt_data.append(dict(Task=t.id, Start=t.start_time, Finish=t.completion_time, Type="Execution"))

if gantt_data:
    df_gantt = pd.DataFrame(gantt_data)
    # Using bar chart as a simple gantt replacement for numeric time
    fig_gantt = px.timeline(df_gantt, x_start="Start", x_end="Finish", y="Task", color="Task", template="plotly_dark")
    # px.timeline expects datetime, but we have integers. We'll hack it or use bar.
    # Hack for integer timeline:
    fig_gantt = px.bar(df_gantt, x="Finish", y="Task", base="Start", orientation='h', color="Task", template="plotly_dark")
    fig_gantt.update_layout(xaxis_title="Time Units", yaxis_title="Task ID", height=400)
    st.plotly_chart(fig_gantt, use_container_width=True)

# Comparison Mode
st.markdown("---")
st.subheader("⚖️ Algorithm Comparison")
if st.checkbox("Enable Side-by-Side Comparison"):
    st.info("Comparing Baseline (Fixed Max Freq) vs Power-Aware (Dynamic DVFS)")
    
    # Run Baseline
    cpu_b = CPU(ambient_temp=ambient_temp)
    class BaselineSimulator(Simulator):
        def apply_power_policy(self):
            self.cpu.set_dvfs_state(len(self.cpu.dvfs_states)-1)
    sim_b = BaselineSimulator(st.session_state.tasks, cpu_b, time_quantum=time_quantum)
    history_b = sim_b.run()
    
    # Run Power-Aware
    cpu_p = CPU(ambient_temp=ambient_temp)
    sim_p = Simulator(st.session_state.tasks, cpu_p, time_quantum=time_quantum)
    history_p = sim_p.run()
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.write("**Baseline**")
        st.write(f"Energy: {cpu_b.total_energy_consumed:.2f} J")
        st.write(f"Peak Temp: {max(history_b['cpu_temp']):.2f} °C")
        st.write(f"Avg Wait: {sum(t.waiting_time for t in sim_b.completed_tasks)/len(sim_b.completed_tasks):.2f}")

    with c2:
        st.write("**Power-Aware**")
        st.write(f"Energy: {cpu_p.total_energy_consumed:.2f} J")
        st.write(f"Peak Temp: {max(history_p['cpu_temp']):.2f} °C")
        st.write(f"Avg Wait: {sum(t.waiting_time for t in sim_p.completed_tasks)/len(sim_p.completed_tasks):.2f}")
    
    energy_saved = (1 - cpu_p.total_energy_consumed / cpu_b.total_energy_consumed) * 100
    st.success(f"🌱 Power-Aware algorithm saved **{energy_saved:.1f}%** energy!")

# Task Table & Export Data Prep
st.markdown("---")
st.subheader("📋 Completed Task Details")
df_tasks = pd.DataFrame([{
    "ID": t.id,
    "Arrival": t.arrival_time,
    "Burst": t.burst_time,
    "Wait Time": f"{t.waiting_time:.2f}",
    "Turnaround": f"{t.turnaround_time:.2f}",
    "Completion": f"{t.completion_time:.2f}"
} for t in sim.completed_tasks])
st.dataframe(df_tasks, use_container_width=True)

# Export
st.sidebar.markdown("---")
csv = df_tasks.to_csv(index=False).encode('utf-8')
st.sidebar.download_button("📥 Export Results (CSV)", data=csv, file_name="simulation_results.csv", mime="text/csv")
