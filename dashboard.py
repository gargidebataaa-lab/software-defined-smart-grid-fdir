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
    layout="wide"
)


# ============================================================
# FILE LOCATIONS
# ============================================================

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

ENGINE_FILE = os.path.join(
    PROJECT_DIR,
    "distribution_network.py"
)

DATA_FILE = os.path.join(
    PROJECT_DIR,
    "stage6_performance_metrics.csv"
)

RESULT_FILE = os.path.join(
    PROJECT_DIR,
    "dashboard_scenario_results.json"
)


# ============================================================
# SCENARIO DEFINITIONS
# ============================================================

SCENARIO_MAP = {
    "Normal Operation": "normal",
    "Feeder Outage": "feeder_outage",
    "Overcurrent Fault": "overcurrent"
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_float(value, default=None):

    try:

        if value is None:
            return default

        if pd.isna(value):
            return default

        return float(value)

    except (TypeError, ValueError):

        return default


def format_value(
    value,
    decimals=2,
    suffix=""
):

    number = safe_float(value)

    if number is None:
        return "N/A"

    return f"{number:.{decimals}f}{suffix}"


def load_csv():

    if not os.path.exists(DATA_FILE):

        return pd.DataFrame()

    try:

        return pd.read_csv(DATA_FILE)

    except Exception as error:

        st.error(
            f"Unable to read performance data: {error}"
        )

        return pd.DataFrame()


def load_result():

    if not os.path.exists(RESULT_FILE):

        return {}

    try:

        with open(
            RESULT_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as error:

        st.warning(
            f"Unable to read scenario result file: {error}"
        )

        return {}


def run_engine(scenario_name):

    environment = os.environ.copy()

    environment["GRID_SCENARIO"] = scenario_name

    try:

        process = subprocess.run(
            [
                sys.executable,
                ENGINE_FILE
            ],
            env=environment,
            capture_output=True,
            text=True,
            timeout=120
        )

        return (
            process.returncode,
            process.stdout,
            process.stderr
        )

    except subprocess.TimeoutExpired:

        return (
            -1,
            "",
            "Simulation timed out after 120 seconds."
        )

    except Exception as error:

        return (
            -1,
            "",
            str(error)
        )


def hour_label(value):

    text = str(value).strip()

    if ":" in text:
        return text

    try:

        return f"{int(round(float(text))):02d}:00"

    except ValueError:

        return text


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚡ Grid Control Panel")

    selected_scenario = st.selectbox(
        "Operating Scenario",
        list(SCENARIO_MAP.keys())
    )

    scenario_name = SCENARIO_MAP[
        selected_scenario
    ]

    st.write("")

    run_button = st.button(
        "▶ Run Digital Twin Simulation",
        width="stretch"
    )

    st.divider()

    st.markdown("### Simulation Scenarios")

    st.write("🟢 Normal Operation")
    st.write("🔴 Feeder Outage")
    st.write("🟠 Overcurrent Fault")


# ============================================================
# RUN SIMULATION
# ============================================================

if run_button:

    with st.spinner(
        "Running Digital Twin simulation..."
    ):

        return_code, stdout, stderr = run_engine(
            scenario_name
        )

    st.session_state["engine_output"] = stdout
    st.session_state["engine_error"] = stderr
    st.session_state["last_scenario"] = scenario_name

    if return_code == 0:

        st.success(
            "Digital Twin simulation completed successfully."
        )

    else:

        st.error(
            "The simulation engine returned an error."
        )

        if stderr:

            st.code(
                stderr,
                language="text"
            )


# ============================================================
# LOAD RESULTS
# ============================================================

df = load_csv()

scenario_result = load_result()


# ============================================================
# PREVENT STALE SCENARIO RESULTS
# ============================================================

result_scenario = scenario_result.get(
    "scenario"
)

if result_scenario is not None:

    if result_scenario != scenario_name:

        scenario_result = {}


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
    "N/A"
)

faulted_element = scenario_result.get(
    "faulted_element",
    "N/A"
)

selected_tie_switch = scenario_result.get(
    "selected_tie_switch"
)

selected_backup_feeder = scenario_result.get(
    "selected_backup_feeder"
)

normal_current = safe_float(
    scenario_result.get(
        "normal_industrial_current_ka"
    )
)

fault_current = safe_float(
    scenario_result.get(
        "fault_current_ka"
    )
)

relay_pickup = safe_float(
    scenario_result.get(
        "relay_pickup_current_ka"
    )
)

restored_voltage = safe_float(
    scenario_result.get(
        "restored_voltage_pu"
    )
)

restored_feeder_loading = safe_float(
    scenario_result.get(
        "restored_feeder_loading_percent"
    )
)

restored_transformer_loading = safe_float(
    scenario_result.get(
        "restored_transformer_loading_percent"
    )
)

active_power_flow_path = scenario_result.get(
    "active_power_flow_path"
)

switch_status = scenario_result.get(
    "switch_status",
    {}
)

event_timeline = scenario_result.get(
    "event_timeline",
    []
)


# ============================================================
# HEADER
# ============================================================

st.title(
    "⚡ Smart Grid Digital Twin"
)

st.caption(
    "Software-Defined Fault Detection, Isolation and Restoration"
)

st.info(
    f"Operating Scenario: **{selected_scenario}**  |  "
    f"Simulation Operating Point: **12:00**"
)


# ============================================================
# GRID STATUS
# ============================================================

st.subheader("🚦 Grid Status")


if scenario_name == "normal":

    st.success(
        "🟢 SYSTEM NORMAL — No grid fault is active."
    )

elif fault_detected and restoration_successful:

    st.success(
        "🟢 FAULT DETECTED → SYSTEM RESTORED"
    )

elif fault_detected:

    st.error(
        "🔴 FAULT DETECTED — Restoration not completed."
    )

else:

    st.warning(
        "🟡 SYSTEM STATUS UNAVAILABLE"
    )


# ============================================================
# FAULT INFORMATION
# ============================================================

st.subheader("🚨 Fault Information")

fault_col1, fault_col2, fault_col3 = st.columns(3)


with fault_col1:

    if fault_detected:

        st.error(
            "🔴 FAULT DETECTED"
        )

    else:

        st.success(
            "🟢 NO FAULT"
        )


with fault_col2:

    st.metric(
        "Fault Type",
        fault_type
    )


with fault_col3:

    st.metric(
        "Affected Element",
        faulted_element
    )


# ============================================================
# PROTECTION SYSTEM
# ============================================================

st.subheader("🛡️ Protection System")

relay_col, breaker_col, pickup_col = st.columns(3)


with relay_col:

    if relay_tripped:

        st.error(
            "🔴 RELAY TRIPPED"
        )

    else:

        st.success(
            "🟢 RELAY HEALTHY"
        )


with breaker_col:

    if breaker_open:

        st.error(
            "🔴 BREAKER OPEN"
        )

    else:

        st.success(
            "🟢 BREAKER CLOSED"
        )


with pickup_col:

    st.metric(
        "Relay Pickup",
        format_value(
            relay_pickup,
            2,
            " kA"
        )
    )


# ============================================================
# RELAY MEASUREMENTS
# ============================================================

st.subheader("📡 Relay Measurements")

relay_measure_col1, relay_measure_col2 = st.columns(2)


with relay_measure_col1:

    st.metric(
        "Normal Feeder Current",
        format_value(
            normal_current,
            3,
            " kA"
        )
    )


with relay_measure_col2:

    st.metric(
        "Fault Current",
        format_value(
            fault_current,
            3,
            " kA"
        )
    )


if (
    fault_current is not None
    and relay_pickup is not None
):

    if fault_current > relay_pickup:

        st.warning(
            f"Measured current "
            f"({fault_current:.3f} kA) exceeded "
            f"relay pickup "
            f"({relay_pickup:.2f} kA)."
        )

    else:

        st.info(
            f"Measured current "
            f"({fault_current:.3f} kA) remained "
            f"below relay pickup."
        )

elif scenario_name == "feeder_outage":

    st.info(
        "This scenario represents a physical feeder outage. "
        "The feeder is unavailable, so an overcurrent relay "
        "trip is not claimed."
    )


# ============================================================
# POWER FLOW / SUPPLY PATH
# ============================================================

st.subheader("🔌 Power Flow / Supply Path")

st.write(
    "The active electrical supply path used by "
    "the Digital Twin is shown below."
)


if restoration_successful:

    if active_power_flow_path:

        flow_path = active_power_flow_path

    else:

        flow_path = [
            "Utility Grid",
            "Backup 11 kV Line",
            "Backup Transformer",
            "Backup LV Bus",
            "Backup Feeder",
            "Tie Switch",
            "Industrial Bus",
            "Industrial Load"
        ]

elif scenario_name == "normal":

    flow_path = [
        "Utility Grid",
        "Main 11 kV Feeder",
        "Main Transformer",
        "415 V Main Bus",
        "Industrial Feeder",
        "Industrial Bus",
        "Industrial Load"
    ]

else:

    flow_path = [
        "Utility Grid",
        "Main 11 kV Feeder",
        "Main Transformer",
        "415 V Main Bus",
        "Industrial Feeder",
        "Industrial Bus",
        "Industrial Load"
    ]


with st.container(border=True):

    for index, node in enumerate(flow_path):

        if index == 0:

            st.markdown(
                f"### ⚡ {node}"
            )

        elif index == len(flow_path) - 1:

            st.markdown(
                f"### 🏭 {node}"
            )

        else:

            st.markdown(
                f"**{node}**"
            )

        if index < len(flow_path) - 1:

            st.markdown(
                "⬇️"
            )


# ============================================================
# SWITCHING STATUS
# ============================================================

st.subheader("🔀 Switching Status")


industrial_breaker_status = (
    "OPEN"
    if breaker_open
    else "CLOSED"
)

normal_tie_status = switch_status.get(
    "Normally Open Tie Switch",
    False
)

alternative_tie_status = switch_status.get(
    "Alternative Tie Switch",
    False
)


switch_col1, switch_col2, switch_col3 = st.columns(3)


with switch_col1:

    if industrial_breaker_status == "OPEN":

        st.error(
            "Industrial Feeder Breaker: OPEN"
        )

    else:

        st.success(
            "Industrial Feeder Breaker: CLOSED"
        )


with switch_col2:

    if normal_tie_status:

        st.success(
            "Normally Open Tie Switch: CLOSED"
        )

    else:

        st.info(
            "Normally Open Tie Switch: OPEN"
        )


with switch_col3:

    if alternative_tie_status:

        st.success(
            "Alternative Tie Switch: CLOSED"
        )

    else:

        st.info(
            "Alternative Tie Switch: OPEN"
        )


# ============================================================
# AUTOMATIC RESTORATION
# ============================================================

st.subheader("🔄 Automatic Restoration")


if restoration_required:

    if restoration_successful:

        st.success(
            "✅ AUTOMATIC RESTORATION SUCCESSFUL"
        )

        st.write(
            "The FDIR controller found a feasible alternate "
            "supply path and restored the affected industrial bus."
        )

        restore_col1, restore_col2, restore_col3 = st.columns(3)


        with restore_col1:

            st.metric(
                "Restored Bus Voltage",
                format_value(
                    restored_voltage,
                    3,
                    " pu"
                )
            )


        with restore_col2:

            st.metric(
                "Backup Feeder Loading",
                format_value(
                    restored_feeder_loading,
                    2,
                    "%"
                )
            )


        with restore_col3:

            st.metric(
                "Backup Transformer Loading",
                format_value(
                    restored_transformer_loading,
                    2,
                    "%"
                )
            )


        if selected_tie_switch:

            st.info(
                f"Selected Tie Switch: **{selected_tie_switch}**"
            )


        if selected_backup_feeder:

            st.info(
                f"Selected Backup Feeder: "
                f"**{selected_backup_feeder}**"
            )


    else:

        st.error(
            "❌ AUTOMATIC RESTORATION FAILED"
        )

        st.write(
            "The FDIR controller could not find a feasible "
            "alternate supply path."
        )

else:

    st.info(
        "No restoration action was required."
    )


# ============================================================
# FDIR CONTROLLER
# ============================================================

st.subheader("🧠 FDIR Controller")

st.write(
    "The Digital Twin follows the following automated "
    "Fault Detection, Isolation and Restoration sequence:"
)

fdir_steps = [
    "🔍 Detect abnormal grid condition",
    "🛡️ Evaluate protection condition",
    "🔌 Isolate affected feeder",
    "🧭 Search alternate network paths",
    "⚡ Test candidate paths using power flow",
    "🔀 Operate the appropriate tie switch",
    "🔄 Restore the affected load",
    "✅ Verify voltage and loading constraints"
]

for step_number, step in enumerate(
    fdir_steps,
    start=1
):

    st.write(
        f"**{step_number}.** {step}"
    )


# ============================================================
# EVENT TIMELINE
# ============================================================

st.subheader("📋 Fault & Restoration Timeline")


if event_timeline:

    for event in event_timeline:

        if isinstance(event, dict):

            event_text = event.get(
                "event",
                str(event)
            )

            event_status = event.get(
                "status",
                ""
            )

            if event_status:

                st.write(
                    f"**{event_status}** — {event_text}"
                )

            else:

                st.write(
                    f"• {event_text}"
                )

        else:

            st.write(
                f"• {event}"
            )

else:

    if scenario_name == "normal":

        st.success(
            "No fault event occurred."
        )

    else:

        timeline_items = []

        if fault_detected:

            timeline_items.append(
                "Fault/abnormal condition detected"
            )

        if relay_tripped:

            timeline_items.append(
                "Protection relay operated"
            )

        if breaker_open:

            timeline_items.append(
                "Industrial feeder breaker opened"
            )

        if restoration_required:

            timeline_items.append(
                "Restoration required"
            )

        if restoration_successful:

            timeline_items.append(
                "Backup supply connected"
            )

            timeline_items.append(
                "Industrial load restored"
            )

        if not timeline_items:

            timeline_items.append(
                "No detailed event information available."
            )

        for item in timeline_items:

            st.write(
                f"• {item}"
            )


# ============================================================
# ELECTRICAL PARAMETERS
# ============================================================

st.subheader("📐 Electrical Parameters")


if not df.empty:

    latest_row = df.iloc[-1]

    parameter_col1, parameter_col2 = st.columns(2)


    with parameter_col1:

        industrial_voltage = safe_float(
            latest_row.get(
                "Industrial_Voltage_pu"
            )
        )

        industrial_loading = safe_float(
            latest_row.get(
                "Industrial_Feeder_Loading_%"
            )
        )

        transformer_loading = safe_float(
            latest_row.get(
                "Main_Transformer_Loading_%"
            )
        )


        st.metric(
            "Industrial Bus Voltage",
            format_value(
                industrial_voltage,
                3,
                " pu"
            )
        )

        st.metric(
            "Industrial Feeder Loading",
            format_value(
                industrial_loading,
                2,
                "%"
            )
        )

        st.metric(
            "Main Transformer Loading",
            format_value(
                transformer_loading,
                2,
                "%"
            )
        )


    with parameter_col2:

        total_losses = safe_float(
            latest_row.get(
                "Total_Losses_MW"
            )
        )

        battery_soc = safe_float(
            latest_row.get(
                "Battery_SOC_%"
            )
        )

        pv_generation = safe_float(
            latest_row.get(
                "PV_MW"
            )
        )

        load_demand = safe_float(
            latest_row.get(
                "Load_MW"
            )
        )


        st.metric(
            "Network Losses",
            format_value(
                total_losses,
                3,
                " MW"
            )
        )

        st.metric(
            "Battery SOC",
            format_value(
                battery_soc,
                2,
                "%"
            )
        )

        st.metric(
            "Solar PV Generation",
            format_value(
                pv_generation,
                2,
                " MW"
            )
        )

        st.metric(
            "Industrial Load",
            format_value(
                load_demand,
                2,
                " MW"
            )
        )


else:

    st.warning(
        "Performance CSV is not available yet."
    )


# ============================================================
# RENEWABLE ENERGY AND BATTERY
# ============================================================

st.subheader("☀️ Renewable Energy & Battery")


if not df.empty:

    renewable_col1, renewable_col2 = st.columns(2)


    with renewable_col1:

        st.markdown(
            "### Solar PV and Load"
        )

        chart_data = df.copy()

        if "Time" in chart_data.columns:

            chart_data["Time_Label"] = (
                chart_data["Time"].apply(
                    hour_label
                )
            )

            chart_data = chart_data.set_index(
                "Time_Label"
            )

        available_columns = [
            column
            for column in [
                "PV_MW",
                "Load_MW"
            ]
            if column in chart_data.columns
        ]

        if available_columns:

            st.line_chart(
                chart_data[
                    available_columns
                ]
            )


    with renewable_col2:

        st.markdown(
            "### Battery State of Charge"
        )

        battery_chart = df.copy()

        if "Time" in battery_chart.columns:

            battery_chart["Time_Label"] = (
                battery_chart["Time"].apply(
                    hour_label
                )
            )

            battery_chart = battery_chart.set_index(
                "Time_Label"
            )

        if "Battery_SOC_%" in battery_chart.columns:

            st.line_chart(
                battery_chart[
                    ["Battery_SOC_%"]
                ]
            )


# ============================================================
# PERFORMANCE TRENDS
# ============================================================

st.subheader("📊 Network Performance Trends")


if not df.empty:

    trend_col1, trend_col2 = st.columns(2)


    with trend_col1:

        st.markdown(
            "### Industrial Bus Voltage"
        )

        voltage_chart = df.copy()

        if "Time" in voltage_chart.columns:

            voltage_chart["Time_Label"] = (
                voltage_chart["Time"].apply(
                    hour_label
                )
            )

            voltage_chart = voltage_chart.set_index(
                "Time_Label"
            )

        if "Industrial_Voltage_pu" in voltage_chart.columns:

            st.line_chart(
                voltage_chart[
                    ["Industrial_Voltage_pu"]
                ]
            )


    with trend_col2:

        st.markdown(
            "### Feeder Loading"
        )

        loading_chart = df.copy()

        if "Time" in loading_chart.columns:

            loading_chart["Time_Label"] = (
                loading_chart["Time"].apply(
                    hour_label
                )
            )

            loading_chart = loading_chart.set_index(
                "Time_Label"
            )

        if "Industrial_Feeder_Loading_%" in loading_chart.columns:

            st.line_chart(
                loading_chart[
                    ["Industrial_Feeder_Loading_%"]
                ]
            )


# ============================================================
# PERFORMANCE SUMMARY
# ============================================================

st.subheader("📈 Performance Summary")


if not df.empty:

    voltage_series = pd.to_numeric(
        df.get(
            "Industrial_Voltage_pu"
        ),
        errors="coerce"
    )

    feeder_series = pd.to_numeric(
        df.get(
            "Industrial_Feeder_Loading_%"
        ),
        errors="coerce"
    )

    transformer_series = pd.to_numeric(
        df.get(
            "Main_Transformer_Loading_%"
        ),
        errors="coerce"
    )

    backup_transformer_series = pd.to_numeric(
        df.get(
            "Backup_Transformer_Loading_%"
        ),
        errors="coerce"
    )


    min_voltage = (
        voltage_series.min()
        if not voltage_series.empty
        else np.nan
    )

    max_feeder_loading = (
        feeder_series.max()
        if not feeder_series.empty
        else np.nan
    )

    max_transformer_loading = (
        transformer_series.max()
        if not transformer_series.empty
        else np.nan
    )

    max_backup_transformer_loading = (
        backup_transformer_series.max()
        if not backup_transformer_series.empty
        else np.nan
    )


    # --------------------------------------------------------
    # TIME AXIS
    # --------------------------------------------------------

    if "Time" in df.columns:

        time_hours = (
            df["Time"]
            .astype(str)
            .apply(
                lambda x:
                int(x.split(":")[0])
                + int(x.split(":")[1]) / 60.0
            )
            .to_numpy(
                dtype=float
            )
        )

    else:

        time_hours = np.arange(
            len(df),
            dtype=float
        )


    # --------------------------------------------------------
    # ENERGY DATA
    # --------------------------------------------------------

    pv_values = pd.to_numeric(
        df.get("PV_MW"),
        errors="coerce"
    ).fillna(0).to_numpy(
        dtype=float
    )

    load_values = pd.to_numeric(
        df.get("Load_MW"),
        errors="coerce"
    ).fillna(0).to_numpy(
        dtype=float
    )

    loss_values = pd.to_numeric(
        df.get("Total_Losses_MW"),
        errors="coerce"
    ).fillna(0).to_numpy(
        dtype=float
    )


    pv_energy = float(
        np.trapezoid(
            pv_values,
            time_hours
        )
    )

    load_energy = float(
        np.trapezoid(
            load_values,
            time_hours
        )
    )

    network_losses = float(
        np.trapezoid(
            loss_values,
            time_hours
        )
    )


    if load_energy > 0:

        pv_coverage = (
            pv_energy
            / load_energy
            * 100
        )

    else:

        pv_coverage = 0.0


    summary_col1, summary_col2, summary_col3 = st.columns(3)


    with summary_col1:

        st.metric(
            "Minimum Industrial Voltage",
            format_value(
                min_voltage,
                3,
                " pu"
            )
        )

        st.metric(
            "Maximum Feeder Loading",
            format_value(
                max_feeder_loading,
                2,
                "%"
            )
        )


    with summary_col2:

        st.metric(
            "Maximum Main Transformer Loading",
            format_value(
                max_transformer_loading,
                2,
                "%"
            )
        )

        st.metric(
            "Maximum Backup Transformer Loading",
            format_value(
                max_backup_transformer_loading,
                2,
                "%"
            )
        )


    with summary_col3:

        st.metric(
            "PV Energy Generated",
            format_value(
                pv_energy,
                3,
                " MWh"
            )
        )

        st.metric(
            "PV Coverage of Load",
            format_value(
                pv_coverage,
                2,
                "%"
            )
        )


    st.metric(
        "Network Loss Energy",
        format_value(
            network_losses,
            3,
            " MWh"
        )
    )


# ============================================================
# POWER FLOW HEALTH
# ============================================================

st.subheader("💚 Power Flow Health")


if (
    not df.empty
    and "Power_Flow_Converged" in df.columns
):

    convergence_values = (
        df["Power_Flow_Converged"]
        .astype(str)
        .str.lower()
    )

    successful_runs = (
        convergence_values == "true"
    ).sum()

    total_runs = len(
        convergence_values
    )

    if successful_runs == total_runs:

        st.success(
            f"All {total_runs} simulated "
            f"power-flow operating points "
            f"converged successfully."
        )

    else:

        st.warning(
            f"{successful_runs} of "
            f"{total_runs} power-flow operating "
            f"points converged."
        )

else:

    st.info(
        "Power-flow convergence information "
        "is not available."
    )


# ============================================================
# COMPLETE SIMULATION DATA
# ============================================================

with st.expander(
    "📋 View Complete Simulation Data"
):

    if not df.empty:

        st.dataframe(
            df,
            width="stretch"
        )

    else:

        st.warning(
            "No simulation data available."
        )


# ============================================================
# ENGINE OUTPUT
# ============================================================

with st.expander(
    "🖥️ View Simulation Engine Output"
):

    engine_output = st.session_state.get(
        "engine_output",
        ""
    )

    engine_error = st.session_state.get(
        "engine_error",
        ""
    )


    if engine_output:

        st.code(
            engine_output,
            language="text"
        )


    if engine_error:

        st.error(
            "Engine error:"
        )

        st.code(
            engine_error,
            language="text"
        )


    if (
        not engine_output
        and not engine_error
    ):

        st.info(
            "Run the Digital Twin simulation "
            "to display engine output."
        )


# ============================================================
# RAW FDIR RESULT
# ============================================================

with st.expander(
    "🔎 View Raw FDIR Result"
):

    if scenario_result:

        st.json(
            scenario_result
        )

    else:

        st.info(
            "No FDIR result is available for "
            "the selected scenario."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Software-Defined Smart Grid | "
    "Digital Twin + NetworkX + Pandapower + FDIR"
)

st.caption(
    "Simulation only — not a real-time protection or "
    "SCADA control system."
)