import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import subprocess
import sys


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Smart Grid Digital Twin",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# HIGH-CONTRAST CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       GENERAL
       ======================================================== */

    .main {
        padding-top: 1rem;
    }

    h1, h2, h3, h4 {
        color: #111111 !important;
    }

    p, span, div, label {
        color: #111111;
    }

    /* ========================================================
       MAIN TITLE
       ======================================================== */

    .main-title {
        font-size: 34px;
        font-weight: 800;
        color: #111111 !important;
        margin-bottom: 4px;
    }

    .subtitle {
        font-size: 17px;
        color: #444444 !important;
        margin-bottom: 20px;
    }

    /* ========================================================
       STATUS CARDS
       ======================================================== */

    .status-card {
        padding: 18px;
        border-radius: 12px;
        margin-bottom: 15px;
        color: #111111 !important;
        font-weight: 600;
    }

    .status-card * {
        color: #111111 !important;
    }

    .fault-card {
        background-color: #fff1f1;
        border: 2px solid #d93025;
    }

    .success-card {
        background-color: #ecfdf3;
        border: 2px solid #188038;
    }

    .normal-card {
        background-color: #eef5ff;
        border: 2px solid #1a73e8;
    }

    .warning-card {
        background-color: #fff8e1;
        border: 2px solid #f9ab00;
    }

    /* ========================================================
       POWER FLOW
       ======================================================== */

    .flow-container {
        margin-top: 10px;
        margin-bottom: 20px;
    }

    .flow-node {
        background-color: #eef7ff;
        border: 2px solid #4285f4;
        border-radius: 10px;
        padding: 14px;
        margin: 6px auto;
        text-align: center;
        max-width: 600px;
        font-weight: 700;
        color: #111111 !important;
    }

    .flow-node * {
        color: #111111 !important;
    }

    .flow-arrow {
        text-align: center;
        font-size: 22px;
        font-weight: 800;
        color: #111111 !important;
        margin: 2px;
    }

    .flow-node-restored {
        background-color: #ecfdf3;
        border: 2px solid #188038;
        border-radius: 10px;
        padding: 14px;
        margin: 6px auto;
        text-align: center;
        max-width: 600px;
        font-weight: 700;
        color: #111111 !important;
    }

    .flow-node-restored * {
        color: #111111 !important;
    }

    /* ========================================================
       TIMELINE
       ======================================================== */

    .timeline-item {
        background-color: #ffffff;
        border: 1px solid #cccccc;
        border-left: 5px solid #4285f4;
        border-radius: 8px;
        padding: 12px 15px;
        margin: 8px 0;
        color: #111111 !important;
    }

    .timeline-item * {
        color: #111111 !important;
    }

    .timeline-success {
        border-left: 5px solid #188038;
        background-color: #f1fff5;
    }

    .timeline-fault {
        border-left: 5px solid #d93025;
        background-color: #fff5f5;
    }

    /* ========================================================
       INFORMATION CARDS
       ======================================================== */

    .info-card {
        background-color: #ffffff;
        border: 1px solid #cccccc;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 12px;
        color: #111111 !important;
    }

    .info-card * {
        color: #111111 !important;
    }

    .info-title {
        font-size: 16px;
        font-weight: 800;
        margin-bottom: 5px;
        color: #111111 !important;
    }

    .info-value {
        font-size: 20px;
        font-weight: 700;
        color: #111111 !important;
    }

    /* ========================================================
       SMALL LABELS
       ======================================================== */

    .small-label {
        font-size: 13px;
        color: #555555 !important;
    }

    /* ========================================================
       SIDEBAR
       ======================================================== */

    [data-testid="stSidebar"] {
        background-color: #f5f7fa;
    }

    [data-testid="stSidebar"] * {
        color: #111111 !important;
    }

    /* ========================================================
       DATAFRAME
       ======================================================== */

    [data-testid="stDataFrame"] {
        color: #111111 !important;
    }

    /* ========================================================
       METRICS
       ======================================================== */

    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #dddddd;
        padding: 10px;
        border-radius: 10px;
    }

    [data-testid="stMetricLabel"] {
        color: #444444 !important;
    }

    [data-testid="stMetricValue"] {
        color: #111111 !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# PROJECT FILE PATHS
# ============================================================

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(
    PROJECT_DIR,
    "stage6_performance_metrics.csv"
)

RESULT_FILE = os.path.join(
    PROJECT_DIR,
    "dashboard_scenario_results.json"
)

ENGINE_FILE = os.path.join(
    PROJECT_DIR,
    "distribution_network.py"
)


# ============================================================
# SCENARIO MAPPING
# ============================================================

SCENARIO_OPTIONS = {
    "Normal Operation": "normal",
    "Feeder Outage": "feeder_outage",
    "Overcurrent Fault": "overcurrent"
}


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⚡ Grid Control Panel")

st.sidebar.markdown(
    """
    <div class="info-card">
        <div class="info-title">Digital Twin</div>
        <div class="small-label">
            Distribution grid simulation and autonomous FDIR
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

selected_scenario_display = st.sidebar.selectbox(
    "Operating Scenario",
    list(SCENARIO_OPTIONS.keys())
)

selected_scenario = SCENARIO_OPTIONS[selected_scenario_display]

st.sidebar.markdown("---")

run_simulation = st.sidebar.button(
    "▶ Run Digital Twin Simulation",
    use_container_width=True
)

st.sidebar.markdown("---")

st.sidebar.markdown(
    """
    **Simulation Features**

    • Newton-Raphson Power Flow  
    • Renewable PV Generation  
    • Battery Storage  
    • Virtual Relay Protection  
    • Fault Detection  
    • Fault Isolation  
    • NetworkX Path Search  
    • Automatic Restoration  
    • Performance Analysis
    """
)


# ============================================================
# PAGE HEADER
# ============================================================

st.markdown(
    '<div class="main-title">⚡ Smart Grid Digital Twin</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="subtitle">
        Software-defined distribution-grid simulation with
        Fault Detection, Isolation and Restoration (FDIR)
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# RUN SIMULATION
# ============================================================

if run_simulation:

    if not os.path.exists(ENGINE_FILE):

        st.error(
            "distribution_network.py was not found in the project folder."
        )

    else:

        with st.spinner(
            f"Running {selected_scenario_display} simulation..."
        ):

            environment = os.environ.copy()

            environment["GRID_SCENARIO"] = selected_scenario

            try:

                process = subprocess.run(
                    [sys.executable, ENGINE_FILE],
                    cwd=PROJECT_DIR,
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                st.session_state["engine_output"] = process.stdout

                st.session_state["engine_error"] = process.stderr

                st.session_state["simulation_ran"] = True

                st.session_state["scenario"] = selected_scenario_display

                if process.returncode == 0:

                    st.success(
                        "Digital Twin simulation completed successfully."
                    )

                else:

                    st.error(
                        "The simulation engine returned an error."
                    )

                    if process.stderr:

                        st.code(
                            process.stderr,
                            language="text"
                        )

            except subprocess.TimeoutExpired:

                st.error(
                    "The simulation took longer than 120 seconds."
                )

            except Exception as error:

                st.error(
                    f"Could not run the simulation: {error}"
                )


# ============================================================
# CHECK WHETHER DATA EXISTS
# ============================================================

if not os.path.exists(DATA_FILE):

    st.warning(
        "No Stage-6 performance data found yet. "
        "Click 'Run Digital Twin Simulation' in the sidebar."
    )

    st.stop()


# ============================================================
# LOAD PERFORMANCE DATA
# ============================================================

try:

    df = pd.read_csv(DATA_FILE)

except Exception as error:

    st.error(
        f"Could not read stage6_performance_metrics.csv: {error}"
    )

    st.stop()


# ============================================================
# LOAD SCENARIO RESULT
# ============================================================

scenario_result = {}

if os.path.exists(RESULT_FILE):

    try:

        with open(
            RESULT_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            scenario_result = json.load(file)

    except Exception as error:

        st.warning(
            f"Could not read dashboard_scenario_results.json: {error}"
        )


# ============================================================
# EXTRACT FDIR RESULTS
# ============================================================

fault_detected = bool(
    scenario_result.get(
        "fault_detected",
        False
    )
)

restoration_required = bool(
    scenario_result.get(
        "restoration_required",
        False
    )
)

restoration_successful = bool(
    scenario_result.get(
        "restoration_successful",
        False
    )
)

relay_tripped = bool(
    scenario_result.get(
        "relay_tripped",
        False
    )
)

breaker_open = bool(
    scenario_result.get(
        "breaker_open",
        False
    )
)

fault_type = scenario_result.get(
    "fault_type",
    "No Fault"
)

faulted_element = scenario_result.get(
    "faulted_element",
    "None"
)

selected_tie_switch = scenario_result.get(
    "selected_tie_switch",
    None
)

selected_backup_feeder = scenario_result.get(
    "selected_backup_feeder",
    None
)

restored_voltage = scenario_result.get(
    "restored_voltage_pu",
    None
)

restored_feeder_loading = scenario_result.get(
    "restored_feeder_loading_percent",
    None
)

restored_transformer_loading = scenario_result.get(
    "restored_transformer_loading_percent",
    None
)

relay_pickup_current = scenario_result.get(
    "relay_pickup_current_ka",
    None
)

normal_industrial_current = scenario_result.get(
    "normal_industrial_current_ka",
    None
)

fault_current = scenario_result.get(
    "fault_current_ka",
    None
)

active_power_flow_path = scenario_result.get(
    "active_power_flow_path",
    None
)


# ============================================================
# BASIC NUMERIC VALUES
# ============================================================

if len(df) == 0:

    st.error("The Stage-6 data file contains no rows.")

    st.stop()


# ============================================================
# SELECT SIMULATION TIME
# ============================================================

simulation_time = "12:00"

if "Time" in df.columns:

    time_values = df["Time"].astype(str).tolist()

    if "12:00" in time_values:

        simulation_time = "12:00"

    else:

        simulation_time = time_values[0]


selected_rows = df[
    df["Time"].astype(str) == simulation_time
]

if len(selected_rows) == 0:

    selected_row = df.iloc[0]

else:

    selected_row = selected_rows.iloc[0]


# ============================================================
# SAFE VALUE FUNCTION
# ============================================================

def safe_float(value, default=0.0):

    try:

        if pd.isna(value):

            return default

        return float(value)

    except Exception:

        return default


# ============================================================
# ELECTRICAL PARAMETERS
# ============================================================

industrial_voltage = safe_float(
    selected_row.get(
        "Industrial_Voltage_pu",
        np.nan
    ),
    0.0
)

industrial_feeder_loading = safe_float(
    selected_row.get(
        "Industrial_Feeder_Loading_%",
        np.nan
    ),
    0.0
)

main_transformer_loading = safe_float(
    selected_row.get(
        "Main_Transformer_Loading_%",
        np.nan
    ),
    0.0
)

network_losses = safe_float(
    selected_row.get(
        "Total_Losses_MW",
        np.nan
    ),
    0.0
)

pv_mw = safe_float(
    selected_row.get(
        "PV_MW",
        np.nan
    ),
    0.0
)

load_mw = safe_float(
    selected_row.get(
        "Load_MW",
        np.nan
    ),
    0.0
)

battery_power = safe_float(
    selected_row.get(
        "Battery_Power_MW",
        np.nan
    ),
    0.0
)

battery_soc = safe_float(
    selected_row.get(
        "Battery_SOC_%",
        np.nan
    ),
    0.0
)

minimum_voltage = safe_float(
    df["Industrial_Voltage_pu"].min()
    if "Industrial_Voltage_pu" in df.columns
    else np.nan,
    0.0
)

maximum_feeder_loading = safe_float(
    df["Industrial_Feeder_Loading_%"].max()
    if "Industrial_Feeder_Loading_%" in df.columns
    else np.nan,
    0.0
)

maximum_main_transformer_loading = safe_float(
    df["Main_Transformer_Loading_%"].max()
    if "Main_Transformer_Loading_%" in df.columns
    else np.nan,
    0.0
)

maximum_backup_transformer_loading = safe_float(
    df["Backup_Transformer_Loading_%"].max()
    if "Backup_Transformer_Loading_%" in df.columns
    else np.nan,
    0.0
)


# ============================================================
# TITLE INFORMATION
# ============================================================

st.markdown(
    f"""
    <div class="info-card">
        <div class="info-title">
            Scenario: {selected_scenario_display}
        </div>

        <div class="small-label">
            Simulation operating point: {simulation_time}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# GRID STATUS
# ============================================================

st.subheader("🚨 Grid Status")


if fault_detected and restoration_successful:

    st.markdown(
        """
        <div class="status-card success-card">
            <h3>⚠️ FAULT DETECTED → SYSTEM RESTORED</h3>

            <p>
                A grid fault was detected and the FDIR controller
                successfully restored the affected load.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

elif fault_detected and not restoration_successful:

    st.markdown(
        """
        <div class="status-card fault-card">
            <h3>🚨 FAULT DETECTED</h3>

            <p>
                A fault was detected, but automatic restoration
                was not successful.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

else:

    st.markdown(
        """
        <div class="status-card normal-card">
            <h3>✅ NORMAL GRID OPERATION</h3>

            <p>
                No fault is currently detected in the selected scenario.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# FAULT INFORMATION
# ============================================================

st.subheader("🔍 Fault & Protection Status")

col1, col2, col3, col4 = st.columns(4)


with col1:

    if fault_detected:

        st.error(
            f"Fault detected\n\n{fault_type}"
        )

    else:

        st.success(
            "No fault detected"
        )


with col2:

    st.write("**Faulted Element**")

    if faulted_element and faulted_element != "None":

        st.warning(
            str(faulted_element)
        )

    else:

        st.success("None")


with col3:

    st.write("**Relay Status**")

    if relay_tripped:

        st.error(
            "🔴 RELAY TRIPPED"
        )

    else:

        st.success(
            "🟢 RELAY HEALTHY"
        )


with col4:

    st.write("**Breaker Status**")

    if breaker_open:

        st.error(
            "🔴 BREAKER OPEN"
        )

    else:

        st.success(
            "🟢 BREAKER CLOSED"
        )


# ============================================================
# RELAY INFORMATION
# ============================================================

st.subheader("🛡️ Relay & Protection Information")

relay_col1, relay_col2, relay_col3 = st.columns(3)


with relay_col1:

    if relay_pickup_current is not None:

        st.metric(
            "Relay Pickup Current",
            f"{safe_float(relay_pickup_current):.2f} kA"
        )

    else:

        st.metric(
            "Relay Pickup Current",
            "N/A"
        )


with relay_col2:

    if normal_industrial_current is not None:

        st.metric(
            "Normal Industrial Current",
            f"{safe_float(normal_industrial_current):.3f} kA"
        )

    else:

        st.metric(
            "Normal Industrial Current",
            "N/A"
        )


with relay_col3:

    if fault_current is not None:

        st.metric(
            "Fault Current",
            f"{safe_float(fault_current):.3f} kA"
        )

    else:

        st.metric(
            "Fault Current",
            "N/A"
        )


# ============================================================
# IMPORTANT RELAY EXPLANATION
# ============================================================

if selected_scenario == "feeder_outage":

    st.info(
        "Feeder outage is represented as an out-of-service feeder. "
        "Therefore, the relay does not need to trip simply because "
        "the feeder was intentionally taken out of service."
    )

elif selected_scenario == "overcurrent":

    if relay_tripped:

        st.success(
            "The simulated overcurrent exceeded the relay pickup "
            "threshold. The virtual relay operated and the feeder "
            "breaker opened."
        )

    else:

        st.warning(
            "An overcurrent scenario was selected, but the exported "
            "relay result does not indicate a relay trip."
        )


# ============================================================
# ELECTRICAL PARAMETERS
# ============================================================

st.subheader("⚡ Electrical Parameters")

p1, p2, p3, p4 = st.columns(4)


with p1:

    st.metric(
        "Industrial Bus Voltage",
        f"{industrial_voltage:.3f} pu"
    )


with p2:

    st.metric(
        "Industrial Feeder Loading",
        f"{industrial_feeder_loading:.2f}%"
    )


with p3:

    st.metric(
        "Main Transformer Loading",
        f"{main_transformer_loading:.2f}%"
    )


with p4:

    st.metric(
        "Network Losses",
        f"{network_losses:.3f} MW"
    )


# ============================================================
# POWER FLOW PATH
# ============================================================

st.subheader("🔌 Power Flow / Supply Path")

st.markdown(
    """
    <div class="small-label">
        The diagram below shows the active logical supply path
        represented by the Digital Twin topology.
    </div>
    """,
    unsafe_allow_html=True
)


# ------------------------------------------------------------
# Build path if engine did not export one
# ------------------------------------------------------------

if active_power_flow_path is None:

    if restoration_successful:

        if selected_backup_feeder:

            active_power_flow_path = [
                "Grid Bus",
                "Backup Feeder Bus",
                "Backup LV Bus",
                "Alternative Backup Bus",
                str(
                    selected_tie_switch
                    if selected_tie_switch
                    else "Tie Switch"
                ),
                "Industrial Bus"
            ]

        else:

            active_power_flow_path = [
                "Grid Bus",
                "Backup Feeder Bus",
                "Backup LV Bus",
                "Industrial Bus"
            ]

    else:

        active_power_flow_path = [
            "Grid Bus",
            "11 kV Feeder Bus",
            "Main Transformer",
            "415 V Main Bus",
            "Industrial Feeder",
            "Industrial Bus"
        ]


# ------------------------------------------------------------
# Handle string path
# ------------------------------------------------------------

if isinstance(
    active_power_flow_path,
    str
):

    active_power_flow_path = [
        item.strip()
        for item in active_power_flow_path.split("->")
        if item.strip()
    ]


# ------------------------------------------------------------
# Draw path
# ------------------------------------------------------------

st.markdown(
    '<div class="flow-container">',
    unsafe_allow_html=True
)

for index, node in enumerate(
    active_power_flow_path
):

    node_text = str(node)

    if restoration_successful:

        st.markdown(
            f"""
            <div class="flow-node-restored">
                ⚡ {node_text}
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            f"""
            <div class="flow-node">
                ⚡ {node_text}
            </div>
            """,
            unsafe_allow_html=True
        )

    if index < len(active_power_flow_path) - 1:

        st.markdown(
            """
            <div class="flow-arrow">
                ↓
            </div>
            """,
            unsafe_allow_html=True
        )

st.markdown(
    "</div>",
    unsafe_allow_html=True
)


# ============================================================
# RESTORATION RESULT
# ============================================================

st.subheader("🔄 Automatic Restoration Result")


if restoration_successful:

    st.markdown(
        """
        <div class="status-card success-card">

            <h3>✅ RESTORATION SUCCESSFUL</h3>

            <p>
                The FDIR controller found a feasible alternate
                supply path and restored the affected industrial bus.
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    r1, r2, r3 = st.columns(3)


    with r1:

        if restored_voltage is not None:

            st.metric(
                "Restored Industrial Voltage",
                f"{safe_float(restored_voltage):.3f} pu"
            )

        else:

            st.metric(
                "Restored Industrial Voltage",
                "N/A"
            )


    with r2:

        if restored_feeder_loading is not None:

            st.metric(
                "Backup Feeder Loading",
                f"{safe_float(restored_feeder_loading):.2f}%"
            )

        else:

            st.metric(
                "Backup Feeder Loading",
                "N/A"
            )


    with r3:

        if restored_transformer_loading is not None:

            st.metric(
                "Backup Transformer Loading",
                f"{safe_float(restored_transformer_loading):.2f}%"
            )

        else:

            st.metric(
                "Backup Transformer Loading",
                "N/A"
            )


    # --------------------------------------------------------
    # Avoid text truncation inside metric boxes
    # --------------------------------------------------------

    r4, r5 = st.columns(2)


    with r4:

        st.write("**Selected Tie Switch**")

        if selected_tie_switch:

            st.success(
                str(selected_tie_switch)
            )

        else:

            st.info("Not available")


    with r5:

        st.write("**Selected Backup Feeder**")

        if selected_backup_feeder:

            st.success(
                str(selected_backup_feeder)
            )

        else:

            st.info("Not available")


elif restoration_required:

    st.markdown(
        """
        <div class="status-card fault-card">

            <h3>⚠️ RESTORATION REQUIRED</h3>

            <p>
                The system identified that restoration was required,
                but a successful restoration result was not available.
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )

else:

    st.markdown(
        """
        <div class="status-card normal-card">

            <h3>ℹ️ NO RESTORATION REQUIRED</h3>

            <p>
                The grid is operating normally at the selected
                simulation operating point.
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# FDIR EVENT TIMELINE
# ============================================================

st.subheader("🧠 FDIR Event Timeline")


timeline = []


if fault_detected:

    timeline.append(
        (
            "timeline-fault",
            "🔴",
            "Fault detected",
            f"Detected condition: {fault_type}"
        )
    )

    timeline.append(
        (
            "timeline-fault",
            "🔌",
            "Faulted element identified",
            str(faulted_element)
        )
    )

    if breaker_open:

        timeline.append(
            (
                "timeline-fault",
                "⚡",
                "Breaker opened",
                "The affected feeder was isolated."
            )
        )

    if relay_tripped:

        timeline.append(
            (
                "timeline-fault",
                "🛡️",
                "Relay operated",
                "The simulated relay exceeded its pickup threshold."
            )
        )

    elif selected_scenario == "feeder_outage":

        timeline.append(
            (
                "timeline-item",
                "ℹ️",
                "Feeder outage isolated",
                "The feeder was taken out of service as the simulated outage."
            )
        )

else:

    timeline.append(
        (
            "timeline-item",
            "🟢",
            "System operating normally",
            "No fault was detected."
        )
    )


if restoration_required:

    timeline.append(
        (
            "timeline-item",
            "🔄",
            "Restoration required",
            "FDIR initiated the restoration process."
        )
    )

    timeline.append(
        (
            "timeline-item",
            "🔎",
            "NetworkX searched restoration paths",
            "Alternative network paths were evaluated."
        )
    )

    timeline.append(
        (
            "timeline-item",
            "📐",
            "Power-flow constraints evaluated",
            "Voltage and equipment loading constraints were checked."
        )
    )


if restoration_successful:

    timeline.append(
        (
            "timeline-success",
            "✅",
            "Feasible backup path selected",
            str(selected_tie_switch)
            if selected_tie_switch
            else "Backup path selected"
        )
    )

    timeline.append(
        (
            "timeline-success",
            "⚡",
            "Industrial load restored",
            "Supply was restored through the selected alternate path."
        )
    )

    timeline.append(
        (
            "timeline-success",
            "✔️",
            "Restoration verified",
            "Voltage and equipment loading remained within the simulated limits."
        )
    )


for css_class, icon, title, description in timeline:

    st.markdown(
        f"""
        <div class="timeline-item {css_class}">

            <strong>
                {icon} {title}
            </strong>

            <br>

            <span>
                {description}
            </span>

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# RENEWABLE ENERGY
# ============================================================

st.subheader("☀️ Renewable Energy")

pv1, pv2, pv3, pv4 = st.columns(4)


pv_surplus = pv_mw - load_mw


if load_mw > 0:

    pv_load_ratio = (
        pv_mw / load_mw
    ) * 100

else:

    pv_load_ratio = 0.0


with pv1:

    st.metric(
        "PV Generation",
        f"{pv_mw:.2f} MW"
    )


with pv2:

    st.metric(
        "Industrial Load",
        f"{load_mw:.2f} MW"
    )


with pv3:

    st.metric(
        "Renewable Surplus",
        f"{pv_surplus:+.2f} MW"
    )


with pv4:

    st.metric(
        "PV-to-Load Ratio",
        f"{pv_load_ratio:.1f}%"
    )


st.info(
    "The PV-to-load ratio is an instantaneous comparison at the "
    "selected simulation time. A value above 100% means PV generation "
    "is greater than the industrial load at that instant."
)


# ============================================================
# BATTERY
# ============================================================

st.subheader("🔋 Battery Storage")

battery1, battery2, battery3 = st.columns(3)


if battery_power > 0:

    battery_status = "CHARGING"

elif battery_power < 0:

    battery_status = "DISCHARGING"

else:

    battery_status = "IDLE"


with battery1:

    st.metric(
        "Battery SOC",
        f"{battery_soc:.2f}%"
    )


with battery2:

    st.metric(
        "Battery Power",
        f"{battery_power:+.3f} MW"
    )


with battery3:

    st.metric(
        "Battery Status",
        battery_status
    )


# ============================================================
# RESTORATION LOGIC
# ============================================================

st.subheader("⚙️ Restoration Logic")

logic_col1, logic_col2 = st.columns(2)


with logic_col1:

    st.markdown(
        """
        <div class="info-card">

            <div class="info-title">
                Detection & Isolation
            </div>

            <p>
                1. Monitor electrical conditions<br>
                2. Detect abnormal condition<br>
                3. Identify affected feeder<br>
                4. Open/disable affected feeder<br>
                5. Isolate the fault
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )


with logic_col2:

    st.markdown(
        """
        <div class="info-card">

            <div class="info-title">
                Restoration
            </div>

            <p>
                1. Search alternate paths using NetworkX<br>
                2. Test candidate paths<br>
                3. Run power-flow calculations<br>
                4. Check voltage/loading constraints<br>
                5. Select feasible path<br>
                6. Restore supply
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# TIME-SERIES PERFORMANCE
# ============================================================

st.subheader("📈 Digital Twin Simulation Trends")


# ------------------------------------------------------------
# Ensure time column is readable
# ------------------------------------------------------------

plot_df = df.copy()

if "Time" in plot_df.columns:

    plot_df["Time"] = plot_df["Time"].astype(str)

    plot_df = plot_df.set_index("Time")


# ------------------------------------------------------------
# Industrial voltage
# ------------------------------------------------------------

if "Industrial_Voltage_pu" in plot_df.columns:

    st.markdown("### Industrial Bus Voltage")

    st.line_chart(
        plot_df[
            ["Industrial_Voltage_pu"]
        ]
    )


# ------------------------------------------------------------
# PV and Load
# ------------------------------------------------------------

pv_load_columns = [
    column
    for column in [
        "PV_MW",
        "Load_MW"
    ]
    if column in plot_df.columns
]

if len(pv_load_columns) > 0:

    st.markdown("### Renewable Generation vs Load")

    st.line_chart(
        plot_df[
            pv_load_columns
        ]
    )


# ------------------------------------------------------------
# Battery SOC
# ------------------------------------------------------------

if "Battery_SOC_%" in plot_df.columns:

    st.markdown("### Battery State of Charge")

    st.line_chart(
        plot_df[
            ["Battery_SOC_%"]
        ]
    )


# ------------------------------------------------------------
# Feeder loading
# ------------------------------------------------------------

if "Industrial_Feeder_Loading_%" in plot_df.columns:

    st.markdown("### Industrial Feeder Loading")

    st.line_chart(
        plot_df[
            ["Industrial_Feeder_Loading_%"]
        ]
    )


# ------------------------------------------------------------
# Transformer loading
# ------------------------------------------------------------

transformer_columns = [
    column
    for column in [
        "Main_Transformer_Loading_%",
        "Backup_Transformer_Loading_%"
    ]
    if column in plot_df.columns
]

if len(transformer_columns) > 0:

    st.markdown("### Transformer Loading")

    st.line_chart(
        plot_df[
            transformer_columns
        ]
    )


# ------------------------------------------------------------
# Network losses
# ------------------------------------------------------------

if "Total_Losses_MW" in plot_df.columns:

    st.markdown("### Network Losses")

    st.line_chart(
        plot_df[
            ["Total_Losses_MW"]
        ]
    )


# ============================================================
# PERFORMANCE SUMMARY
# ============================================================

st.subheader("📊 Performance Summary")


# ------------------------------------------------------------
# Calculate energy using numeric time
# ------------------------------------------------------------

if "Time" in df.columns:

    def convert_time_to_hours(value):

        value = str(value).strip()

        if ":" in value:

            parts = value.split(":")

            try:

                return (
                    int(parts[0])
                    + int(parts[1]) / 60.0
                )

            except Exception:

                return np.nan

        try:

            return float(value)

        except Exception:

            return np.nan


    energy_time = (
        df["Time"]
        .apply(convert_time_to_hours)
        .to_numpy(dtype=float)
    )

else:

    energy_time = np.arange(
        len(df),
        dtype=float
    )


# ------------------------------------------------------------
# PV energy
# ------------------------------------------------------------

if "PV_MW" in df.columns:

    pv_energy = np.trapezoid(
        df["PV_MW"]
        .fillna(0)
        .to_numpy(dtype=float),
        energy_time
    )

else:

    pv_energy = 0.0


# ------------------------------------------------------------
# Load energy
# ------------------------------------------------------------

if "Load_MW" in df.columns:

    load_energy = np.trapezoid(
        df["Load_MW"]
        .fillna(0)
        .to_numpy(dtype=float),
        energy_time
    )

else:

    load_energy = 0.0


# ------------------------------------------------------------
# Network losses energy
# ------------------------------------------------------------

if "Total_Losses_MW" in df.columns:

    losses_energy = np.trapezoid(
        df["Total_Losses_MW"]
        .fillna(0)
        .to_numpy(dtype=float),
        energy_time
    )

else:

    losses_energy = 0.0


if load_energy > 0:

    pv_coverage = (
        pv_energy / load_energy
    ) * 100

else:

    pv_coverage = 0.0


summary1, summary2, summary3, summary4 = st.columns(4)


with summary1:

    st.metric(
        "Minimum Industrial Voltage",
        f"{minimum_voltage:.3f} pu"
    )


with summary2:

    st.metric(
        "Maximum Feeder Loading",
        f"{maximum_feeder_loading:.2f}%"
    )


with summary3:

    st.metric(
        "Maximum Main Transformer",
        f"{maximum_main_transformer_loading:.2f}%"
    )


with summary4:

    st.metric(
        "PV Energy Generated",
        f"{pv_energy:.3f} MWh"
    )


summary5, summary6, summary7, summary8 = st.columns(4)


with summary5:

    st.metric(
        "Load Energy Demand",
        f"{load_energy:.3f} MWh"
    )


with summary6:

    st.metric(
        "Network Loss Energy",
        f"{losses_energy:.3f} MWh"
    )


with summary7:

    st.metric(
        "PV Coverage of Load",
        f"{pv_coverage:.2f}%"
    )


with summary8:

    st.metric(
        "Maximum Backup Transformer",
        f"{maximum_backup_transformer_loading:.2f}%"
    )


# ============================================================
# RESTORATION PERFORMANCE
# ============================================================

st.subheader("🔄 Restoration Performance")


if restoration_successful:

    rp1, rp2, rp3 = st.columns(3)


    with rp1:

        if restored_voltage is not None:

            st.metric(
                "Restored Voltage",
                f"{safe_float(restored_voltage):.3f} pu"
            )

        else:

            st.metric(
                "Restored Voltage",
                "N/A"
            )


    with rp2:

        if restored_feeder_loading is not None:

            st.metric(
                "Backup Feeder Loading",
                f"{safe_float(restored_feeder_loading):.2f}%"
            )

        else:

            st.metric(
                "Backup Feeder Loading",
                "N/A"
            )


    with rp3:

        if restored_transformer_loading is not None:

            st.metric(
                "Backup Transformer Loading",
                f"{safe_float(restored_transformer_loading):.2f}%"
            )

        else:

            st.metric(
                "Backup Transformer Loading",
                "N/A"
            )


    st.markdown(
        f"""
        <div class="status-card success-card">

            <h4>
                Automatic Restoration Completed
            </h4>

            <p>
                Supply restored through:
                <strong>
                    {selected_tie_switch
                    if selected_tie_switch
                    else "selected tie switch"}
                </strong>
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )

else:

    st.info(
        "No successful automatic restoration result is available "
        "for the selected scenario."
    )


# ============================================================
# POWER FLOW HEALTH
# ============================================================

st.subheader("🧮 Power Flow Health")


if "Power_Flow_Converged" in df.columns:

    convergence_values = (
        df["Power_Flow_Converged"]
        .astype(str)
        .str.lower()
    )

    converged_count = (
        convergence_values
        .isin(["true", "1", "yes"])
        .sum()
    )

    total_count = len(df)

    if converged_count == total_count:

        st.success(
            f"Newton-Raphson power flow converged at "
            f"all {total_count} simulated time points."
        )

    else:

        st.warning(
            f"Power flow converged at "
            f"{converged_count} of {total_count} "
            f"simulated time points."
        )

else:

    st.info(
        "Power-flow convergence information is not available "
        "in the exported performance data."
    )


# ============================================================
# COMPLETE SIMULATION DATA
# ============================================================

st.subheader("📋 Complete Simulation Data")

st.dataframe(
    df,
    width="stretch",
    hide_index=True
)


# ============================================================
# ENGINE OUTPUT
# ============================================================

if "engine_output" in st.session_state:

    with st.expander(
        "🖥️ Simulation Engine Output"
    ):

        st.code(
            st.session_state["engine_output"],
            language="text"
        )


if "engine_error" in st.session_state:

    if st.session_state["engine_error"]:

        with st.expander(
            "⚠️ Simulation Engine Messages"
        ):

            st.code(
                st.session_state["engine_error"],
                language="text"
            )


# ============================================================
# RAW SCENARIO RESULT
# ============================================================

with st.expander(
    "🔧 Raw FDIR Scenario Result"
):

    st.json(
        scenario_result
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    """
    <div style="
        text-align:center;
        color:#555555 !important;
        padding:10px;
    ">
        <strong>Software-Defined Smart Grid Digital Twin</strong><br>
        Fault Detection • Isolation • Restoration • Renewable Integration
    </div>
    """,
    unsafe_allow_html=True
)