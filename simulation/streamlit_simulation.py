import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time

ELECTRON_CHARGE = 1.602e-19  

# Function to calculate effective T1
def effective_T1(T1_initial, beam_current):
    """Calculate effective T1 due to beam heating."""
    return T1_initial / (1 + 0.1 * beam_current)

# Polarization degradation model
def polarization_model(P, T1, beta, P_thermal, dt, microwave_effect):
    """Compute the next polarization value, modified by microwave adjustment."""
    dP_dt = -(P - P_thermal) / T1 - beta * P + microwave_effect
    return P + dP_dt * dt

# Initialize session state for simulation variables
if "running" not in st.session_state:
    st.session_state.running = False
if "microwave_frequency" not in st.session_state:
    st.session_state.microwave_frequency = 140.1
if "polarization" not in st.session_state:
    st.session_state.polarization = 0.9
if "time_steps" not in st.session_state:
    st.session_state.time_steps = []
if "polarization_history" not in st.session_state:
    st.session_state.polarization_history = []
if "frequency_history" not in st.session_state:
    st.session_state.frequency_history = []
if "dose_history" not in st.session_state:
    st.session_state.dose_history = []
if "accumulated_dose" not in st.session_state:
    st.session_state.accumulated_dose = 0.0

# App layout
st.title("Interactive Polarization Simulation")
st.sidebar.header("Simulation Controls")

# Sidebar inputs for simulation parameters
P_thermal = st.sidebar.slider("Thermal Polarization (P_thermal)", 0.0, 0.2, 0.05, 0.01)
T1_initial = st.sidebar.number_input("Initial T1 (seconds)", min_value=1, max_value=1000, value=300, step=10)
beam_current = st.sidebar.number_input("Beam Current (A)", min_value=1e-9, max_value=1e-3, value=2e-9, step=1e-9, format="%.1e")
radiation_coeff = st.sidebar.number_input("Radiation Coefficient", min_value=1e-6, max_value=1e-2, value=0.0001, format="%.5f")
time_step = st.sidebar.slider("Time Step (seconds)", 0.1, 10.0, 1.0, 0.1)
beam_area = st.sidebar.number_input("Beam Area (cm²)", min_value=0.1, max_value=10.0, value=1.0, step=0.1)

# Microwave frequency adjustment buttons
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Increase Frequency"):
        st.session_state.microwave_frequency += 0.1
with col2:
    if st.button("Decrease Frequency"):
        st.session_state.microwave_frequency -= 0.1

# Start/Stop button
col3, col4 = st.columns([1, 1])
with col3:
    if st.button("Start Simulation"):
        st.session_state.running = True
with col4:
    if st.button("Stop Simulation"):
        st.session_state.running = False

# Display current microwave frequency
st.write(f"### Current Microwave Frequency: {st.session_state.microwave_frequency:.1f} GHz")

# Create containers for the plots
plot_columns = st.columns(3)
polarization_plot = plot_columns[0].empty()
frequency_plot = plot_columns[1].empty()
dose_plot = plot_columns[2].empty()

# Continuous simulation loop
while st.session_state.running:
    # Calculate effective T1
    T1 = effective_T1(T1_initial, beam_current)

    # Compute microwave effect based on deviation from 140.1 GHz
    microwave_effect = -(st.session_state.microwave_frequency - 140.1) * 0.01

    # Update polarization
    polarization = polarization_model(
        st.session_state.polarization, T1, radiation_coeff, P_thermal, time_step, microwave_effect
    )
    st.session_state.polarization = max(0, polarization)  # Ensure polarization doesn't go below 0

    # Update accumulated dose
    st.session_state.accumulated_dose += (beam_current * time_step) / (ELECTRON_CHARGE * beam_area)
    st.session_state.dose_history.append(st.session_state.accumulated_dose)

    # Append to history
    time_step_index = len(st.session_state.time_steps) * time_step
    st.session_state.time_steps.append(time_step_index)
    st.session_state.polarization_history.append(st.session_state.polarization)
    st.session_state.frequency_history.append(st.session_state.microwave_frequency)

    # Ensure all histories are the same length
    if len(st.session_state.dose_history) > len(st.session_state.time_steps):
        st.session_state.dose_history = st.session_state.dose_history[:len(st.session_state.time_steps)]

    # Update Polarization Plot
    fig1, ax1 = plt.subplots()
    ax1.scatter(st.session_state.time_steps, st.session_state.polarization_history, label="Polarization", color="blue")
    ax1.set_title("Polarization Over Time")
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Polarization")
    ax1.legend()
    ax1.grid()
    polarization_plot.pyplot(fig1)
    plt.close(fig1)

    # Update Microwave Frequency Plot
    fig2, ax2 = plt.subplots()
    ax2.scatter(st.session_state.time_steps, st.session_state.frequency_history, label="Microwave Frequency", color="purple")
    ax2.set_title("Microwave Frequency Over Time")
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Frequency (GHz)")
    ax2.legend()
    ax2.grid()
    frequency_plot.pyplot(fig2)
    plt.close(fig2)

    # Update Accumulated Dose Plot
    fig3, ax3 = plt.subplots()
    ax3.scatter(st.session_state.time_steps, st.session_state.dose_history, label="Accumulated Dose", color="green")
    ax3.set_title("Accumulated Dose Over Time")
    ax3.set_xlabel("Time (s)")
    ax3.set_ylabel("Accumulated Dose (e-/cm²)")
    ax3.legend()
    ax3.grid()
    dose_plot.pyplot(fig3)
    plt.close(fig3)

    # Pause for the time step duration to simulate real-time updates
    time.sleep(time_step)
