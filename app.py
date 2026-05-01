import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
        border: 1px solid #3e4451;
    }
    h1, h2, h3 {
        color: #00d4ff;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #1e2130;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00d4ff22;
        border-bottom: 2px solid #00d4ff;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Advanced Power-Aware CPU Scheduler")
st.markdown("### Energy-Efficient & Thermal-Aware Scheduling Simulation")

# Sidebar Configuration
st.sidebar.header("🛠️ Simulation Parameters")
num_tasks = st.sidebar.slider("Number of Tasks", 5, 50, 20)
ambient_temp = st.sidebar.slider("Ambient Temperature (°C)", 10.0, 45.0, 25.0)
time_quantum = st.sidebar.slider("Round Robin Quantum", 1, 10, 2)

# Task Generation
def generate_tasks(n):
    tasks = []
    for i in range(n):
        arrival = random.randint(0, 30)
        burst = random.randint(5, 40)
        tasks.append(Task(f"T{i+1}", arrival, burst))
    return tasks

if 'tasks' not in st.session_state:
    st.session_state.tasks = generate_tasks(num_tasks)

if st.sidebar.button("🔄 Regenerate Tasks"):
    st.session_state.tasks = generate_tasks(num_tasks)
    st.rerun()

# Run Both Simulations for Comparison
@st.cache_data
def run_simulations(_tasks, ambient_temp, time_quantum):
    # Baseline
    cpu_b = CPU(ambient_temp=ambient_temp)
    sim_b = Simulator(_tasks, cpu_b, time_quantum=time_quantum, is_baseline=True)
    hist_b = sim_b.run()
    tasks_b = sim_b.completed_tasks
    
    # Power-Aware
    cpu_p = CPU(ambient_temp=ambient_temp)
    sim_p = Simulator(_tasks, cpu_p, time_quantum=time_quantum, is_baseline=False)
    hist_p = sim_p.run()
    tasks_p = sim_p.completed_tasks
    
    return (hist_b, tasks_b, cpu_b.total_energy_consumed), (hist_p, tasks_p, cpu_p.total_energy_consumed)

(hist_b, tasks_b, energy_b), (hist_p, tasks_p, energy_p) = run_simulations(st.session_state.tasks, ambient_temp, time_quantum)

# Tabs for organization
tab1, tab2, tab3 = st.tabs(["📊 Performance Dashboard", "⚖️ Energy Comparison", "📋 Task Logs"])

with tab1:
    st.subheader("📈 Real-time CPU Telemetry (Power-Aware Mode)")
    df_hist = pd.DataFrame(hist_p)
    
    # Create subplots with shared x-axis
    fig = make_subplots(rows=2, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.1,
                        subplot_titles=("Thermal & Frequency", "Power Consumption"))
    
    # Row 1: Temp and Freq
    fig.add_trace(go.Scatter(x=df_hist["time"], y=df_hist["cpu_temp"], name="Temp (°C)", 
                             line=dict(color="#ff4b4b", width=3)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_hist["time"], y=df_hist["cpu_freq"] * 25, name="Freq (Scale x25)", 
                             line=dict(color="#00d4ff", width=2, dash='dot')), row=1, col=1)
    # Throttling line
    fig.add_hline(y=75, line_dash="dash", line_color="orange", annotation_text="Thermal Limit", row=1, col=1)
    
    # Row 2: Power
    fig.add_trace(go.Scatter(x=df_hist["time"], y=df_hist["cpu_power"], name="Power (W)", 
                             fill='tozeroy', line=dict(color="#00ff00", width=2)), row=2, col=1)
    
    fig.update_layout(template="plotly_dark", height=600, hovermode="x unified", margin=dict(t=50, b=50))
    st.plotly_chart(fig, use_container_width=True)

    # Gantt Chart
    st.subheader("🗓️ Task Execution Timeline")
    gantt_data = []
    for t in tasks_p:
        gantt_data.append(dict(Task=t.id, Start=t.start_time, Finish=t.completion_time, Type="Execution"))
    
    if gantt_data:
        df_gantt = pd.DataFrame(gantt_data)
        fig_gantt = px.bar(df_gantt, x="Finish", y="Task", base="Start", orientation='h', 
                          color="Task", template="plotly_dark",
                          labels={"Finish": "Time Units", "Task": "Process ID"})
        fig_gantt.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_gantt, use_container_width=True)

with tab2:
    st.subheader("⚖️ Baseline (Fixed) vs Power-Aware (DVFS)")
    
    # Top Level Savings Metric
    energy_savings = (1 - energy_p / energy_b) * 100
    avg_wait_b = sum(t.waiting_time for t in tasks_b) / len(tasks_b)
    avg_wait_p = sum(t.waiting_time for t in tasks_p) / len(tasks_p)
    peak_temp_b = max(hist_b["cpu_temp"])
    peak_temp_p = max(hist_p["cpu_temp"])
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Energy Savings", f"{energy_savings:.1f}%", f"{(energy_b - energy_p):.1f} Joules Saved")
    m2.metric("Thermal Reduction", f"{(peak_temp_b - peak_temp_p):.1f} °C", f"{peak_temp_p:.1f} °C Peak", delta_color="normal")
    m3.metric("Latency Trade-off", f"{(avg_wait_p - avg_wait_b):.1f} units", "Added Wait Time", delta_color="inverse")

    # Comparison Charts
    st.markdown("---")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("#### 🔋 Total Energy Consumption")
        df_energy = pd.DataFrame({
            "Policy": ["Baseline", "Power-Aware"],
            "Energy (J)": [energy_b, energy_p]
        })
        fig_energy = px.bar(df_energy, x="Policy", y="Energy (J)", color="Policy",
                           color_discrete_map={"Baseline": "#636EFA", "Power-Aware": "#00CC96"},
                           template="plotly_dark")
        st.plotly_chart(fig_energy, use_container_width=True)

    with col_b:
        st.markdown("#### 🌡️ Thermal Profile Comparison")
        fig_temp_comp = go.Figure()
        fig_temp_comp.add_trace(go.Scatter(x=hist_b["time"], y=hist_b["cpu_temp"], name="Baseline Temp", line=dict(color="#636EFA", width=1.5)))
        fig_temp_comp.add_trace(go.Scatter(x=hist_p["time"], y=hist_p["cpu_temp"], name="Power-Aware Temp", line=dict(color="#00CC96", width=2)))
        fig_temp_comp.update_layout(template="plotly_dark", xaxis_title="Time", yaxis_title="Temp (°C)", height=400, margin=dict(t=20, b=20))
        st.plotly_chart(fig_temp_comp, use_container_width=True)

    st.markdown("#### 📉 Cumulative Energy Consumption Over Time")
    fig_energy_time = go.Figure()
    fig_energy_time.add_trace(go.Scatter(x=hist_b["time"], y=hist_b["cumulative_energy"], name="Baseline Energy", line=dict(color="#636EFA", dash='dot')))
    fig_energy_time.add_trace(go.Scatter(x=hist_p["time"], y=hist_p["cumulative_energy"], name="Power-Aware Energy", line=dict(color="#00CC96", width=3)))
    fig_energy_time.update_layout(template="plotly_dark", xaxis_title="Time Units", yaxis_title="Energy (Joules)", height=400)
    st.plotly_chart(fig_energy_time, use_container_width=True)

    st.markdown("#### ⏳ Performance vs Efficiency Trade-off")
    # Multi-metric comparison
    metrics_data = {
        "Metric": ["Energy (kJ/10)", "Avg Wait Time", "Peak Temp (°C/10)"],
        "Baseline": [energy_b/10, avg_wait_b, peak_temp_b/10],
        "Power-Aware": [energy_p/10, avg_wait_p, peak_temp_p/10]
    }
    df_metrics = pd.DataFrame(metrics_data)
    fig_metrics = go.Figure(data=[
        go.Bar(name='Baseline', x=df_metrics["Metric"], y=df_metrics["Baseline"], marker_color='#636EFA'),
        go.Bar(name='Power-Aware', x=df_metrics["Metric"], y=df_metrics["Power-Aware"], marker_color='#00CC96')
    ])
    fig_metrics.update_layout(barmode='group', template="plotly_dark", height=400)
    st.plotly_chart(fig_metrics, use_container_width=True)

with tab3:
    st.subheader("📋 Task Execution Details")
    
    # Selector for which data to view
    view_policy = st.radio("View Results For:", ["Power-Aware", "Baseline"], horizontal=True)
    current_tasks = tasks_p if view_policy == "Power-Aware" else tasks_b
    
    df_tasks = pd.DataFrame([{
        "ID": t.id,
        "Arrival": t.arrival_time,
        "Burst": t.burst_time,
        "Wait Time": round(t.waiting_time, 2),
        "Turnaround": round(t.turnaround_time, 2),
        "Completion": round(t.completion_time, 2)
    } for t in current_tasks])
    
    st.dataframe(df_tasks, use_container_width=True)
    
    # Download section
    csv = df_tasks.to_csv(index=False).encode('utf-8')
    st.download_button(f"📥 Download {view_policy} Results (CSV)", data=csv, file_name=f"sim_{view_policy.lower()}.csv", mime="text/csv")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("""
**Algorithm Insights:**
- **DVFS**: Dynamic Voltage & Frequency Scaling reduces power by lowering frequency during low load.
- **Thermal Awareness**: Throttles CPU when temp > 75°C to prevent hardware damage.
- **Round Robin**: Ensures fair CPU time sharing among all tasks.
""")
