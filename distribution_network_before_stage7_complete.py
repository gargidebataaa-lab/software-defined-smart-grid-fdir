import pandapower as pp
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import os
import json

from networkx_engine import find_restoration_paths


# ============================================================
# SOFTWARE-DEFINED SMART GRID
# DIGITAL TWIN BASED FDIR SIMULATION
# VERSION 3
# ============================================================

print("\n======================================================")
print(" SOFTWARE-DEFINED SMART GRID")
print(" DIGITAL TWIN BASED FDIR SIMULATION")
print(" VERSION 3")
print("======================================================\n")


# ============================================================
# STAGE 2 - FAULT SCENARIO SELECTION
# ============================================================

# Choose one:
#
# "overcurrent"   -> Industrial load increases and relay trips
# "feeder_outage" -> Industrial feeder becomes unavailable
# "normal"        -> No fault condition
#

SCENARIO = os.environ.get("GRID_SCENARIO", "feeder_outage")


# ============================================================
# STAGE 3 - RENEWABLE ENERGY SCENARIO
# ============================================================

# Choose one:
#
# "sunny"       -> Normal solar generation
# "high_solar"  -> High solar generation / solar surplus
# "cloudy"      -> Reduced solar generation
# "night"       -> No solar generation
#

PV_SCENARIO = "high_solar"


# ============================================================
# BATTERY OPERATING MODE
# ============================================================

# "auto"  -> Intelligent automatic battery control
# "idle"  -> Battery remains idle
#
# In AUTO mode:
#
# PV > Load  -> Battery charges
# PV < Load  -> Battery discharges
# SOC low    -> Battery stops discharging
# SOC high   -> Battery stops charging
#

BATTERY_MODE = "auto"


print("PV Scenario:", PV_SCENARIO)
print("Battery Mode:", BATTERY_MODE)
print("Selected Fault Scenario:", SCENARIO)


# ============================================================
# STEP 1 - CREATE NETWORK
# ============================================================

net = pp.create_empty_network(
    name="Digital Twin Smart Distribution Grid"
)


# ============================================================
# STEP 2 - CREATE BUSES
# ============================================================

# ------------------------------------------------------------
# 11 kV BUSES
# ------------------------------------------------------------

bus_grid = pp.create_bus(
    net,
    vn_kv=11.0,
    name="Grid Bus"
)

bus_main = pp.create_bus(
    net,
    vn_kv=11.0,
    name="Main Feeder Bus"
)

bus_backup = pp.create_bus(
    net,
    vn_kv=11.0,
    name="Backup Feeder Bus"
)


# ------------------------------------------------------------
# 415 V BUSES
# ------------------------------------------------------------

bus_lv_main = pp.create_bus(
    net,
    vn_kv=0.415,
    name="Main LV Bus"
)

bus_residential = pp.create_bus(
    net,
    vn_kv=0.415,
    name="Residential Bus"
)

bus_industrial = pp.create_bus(
    net,
    vn_kv=0.415,
    name="Industrial Bus"
)

bus_lv_backup = pp.create_bus(
    net,
    vn_kv=0.415,
    name="Backup LV Bus"
)

bus_backup_remote_lv = pp.create_bus(
    net,
    vn_kv=0.415,
    name="Backup Remote LV Bus"
)

bus_backup_alt = pp.create_bus(
    net,
    vn_kv=0.415,
    name="Alternative Backup Bus"
)


# ============================================================
# STEP 3 - EXTERNAL GRID
# ============================================================

grid = pp.create_ext_grid(
    net,
    bus=bus_grid,
    vm_pu=1.0,
    name="Utility Grid"
)


# ============================================================
# STEP 4 - MAIN 11 kV FEEDER
# ============================================================

main_line = pp.create_line_from_parameters(
    net,
    from_bus=bus_grid,
    to_bus=bus_main,
    length_km=2.0,
    r_ohm_per_km=0.15,
    x_ohm_per_km=0.40,
    c_nf_per_km=10,
    max_i_ka=0.40,
    name="Main 11kV Line"
)


# ============================================================
# STEP 5 - BACKUP 11 kV FEEDER
# ============================================================

backup_line = pp.create_line_from_parameters(
    net,
    from_bus=bus_grid,
    to_bus=bus_backup,
    length_km=2.5,
    r_ohm_per_km=0.15,
    x_ohm_per_km=0.40,
    c_nf_per_km=10,
    max_i_ka=0.40,
    name="Backup 11kV Line"
)


# ============================================================
# STEP 6 - MAIN LV FEEDERS
# ============================================================

residential_line = pp.create_line_from_parameters(
    net,
    from_bus=bus_lv_main,
    to_bus=bus_residential,
    length_km=0.10,
    r_ohm_per_km=0.05,
    x_ohm_per_km=0.05,
    c_nf_per_km=10,
    max_i_ka=1.0,
    name="Residential Feeder"
)


industrial_line = pp.create_line_from_parameters(
    net,
    from_bus=bus_lv_main,
    to_bus=bus_industrial,
    length_km=0.15,
    r_ohm_per_km=0.05,
    x_ohm_per_km=0.05,
    c_nf_per_km=10,
    max_i_ka=1.0,
    name="Industrial Feeder"
)


# ============================================================
# STEP 7 - BACKUP LV FEEDERS
# ============================================================

# Normal backup path:
#
# Backup Transformer
#       |
# Backup LV Bus
#       |
# Backup LV Feeder
#       |
# Backup Remote LV Bus
#       |
# Normally Open Tie
#       |
# Industrial Bus
#

backup_lv_line = pp.create_line_from_parameters(
    net,
    from_bus=bus_lv_backup,
    to_bus=bus_backup_remote_lv,
    length_km=0.10,
    r_ohm_per_km=0.05,
    x_ohm_per_km=0.05,
    c_nf_per_km=10,
    max_i_ka=0.50,
    name="Backup LV Feeder"
)


# ------------------------------------------------------------
# Alternative backup path
# ------------------------------------------------------------

alternative_backup_line = pp.create_line_from_parameters(
    net,
    from_bus=bus_lv_backup,
    to_bus=bus_backup_alt,
    length_km=0.05,
    r_ohm_per_km=0.03,
    x_ohm_per_km=0.03,
    c_nf_per_km=10,
    max_i_ka=2.0,
    name="Alternative Backup Feeder"
)


# ============================================================
# STEP 8 - TRANSFORMERS
# ============================================================

main_trafo = pp.create_transformer_from_parameters(
    net,
    hv_bus=bus_main,
    lv_bus=bus_lv_main,
    sn_mva=2.5,
    vn_hv_kv=11.0,
    vn_lv_kv=0.415,
    vk_percent=10.0,
    vkr_percent=0.5,
    pfe_kw=0,
    i0_percent=0,
    shift_degree=0,
    name="Main Transformer"
)


backup_trafo = pp.create_transformer_from_parameters(
    net,
    hv_bus=bus_backup,
    lv_bus=bus_lv_backup,
    sn_mva=2.5,
    vn_hv_kv=11.0,
    vn_lv_kv=0.415,
    vk_percent=10.0,
    vkr_percent=0.5,
    pfe_kw=0,
    i0_percent=0,
    shift_degree=0,
    name="Backup Transformer"
)


# ============================================================
# STEP 9 - CIRCUIT BREAKER AND TIE SWITCHES
# ============================================================

industrial_breaker = pp.create_switch(
    net,
    bus=bus_lv_main,
    element=industrial_line,
    et="l",
    closed=True,
    type="CB",
    name="Industrial Feeder Breaker"
)


normal_tie_switch = pp.create_switch(
    net,
    bus=bus_industrial,
    element=bus_backup_remote_lv,
    et="b",
    closed=False,
    type="CB",
    name="Normally Open Tie Switch"
)


alternative_tie_switch = pp.create_switch(
    net,
    bus=bus_industrial,
    element=bus_backup_alt,
    et="b",
    closed=False,
    type="CB",
    name="Alternative Tie Switch"
)


# ============================================================
# STEP 10 - LOADS
# ============================================================

residential_load = pp.create_load(
    net,
    bus=bus_residential,
    p_mw=0.30,
    q_mvar=0.10,
    name="Residential Load"
)


industrial_load = pp.create_load(
    net,
    bus=bus_industrial,
    p_mw=0.50,
    q_mvar=0.20,
    name="Industrial Load"
)


# ============================================================
# STEP 11 - SOLAR PV SYSTEM + DYNAMIC BATTERY SOC SIMULATION
# ============================================================

print("\n============================================================")
print("STEP 11 - RENEWABLE ENERGY + DYNAMIC BATTERY SIMULATION")
print("============================================================")

print(f"PV Scenario: {PV_SCENARIO}")

simulation_hours = np.array([8, 10, 12, 14, 16, 18, 20], dtype=float)

industrial_load_profile = np.array([
    0.35, 0.40, 0.50, 0.50, 0.45, 0.40, 0.35
])

pv_profiles = {
    "sunny": np.array([0.15, 0.25, 0.25, 0.22, 0.15, 0.05, 0.00]),
    "high_solar": np.array([0.25, 0.40, 0.65, 0.60, 0.40, 0.15, 0.00]),
    "cloudy": np.array([0.08, 0.12, 0.12, 0.10, 0.06, 0.02, 0.00]),
    "night": np.array([0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00])
}

if PV_SCENARIO not in pv_profiles:
    raise ValueError(
        f"Unknown PV_SCENARIO '{PV_SCENARIO}'. "
        f"Available scenarios: {list(pv_profiles.keys())}"
    )

pv_profile = pv_profiles[PV_SCENARIO]

SIMULATION_HOUR = 12

if SIMULATION_HOUR not in simulation_hours:
    raise ValueError(
        f"SIMULATION_HOUR must be one of {simulation_hours.tolist()}"
    )

selected_index = np.where(
    simulation_hours == SIMULATION_HOUR
)[0][0]

pv_power = float(pv_profile[selected_index])
industrial_load_demand = float(industrial_load_profile[selected_index])

net.load.at[industrial_load, "p_mw"] = industrial_load_demand

pv_system = pp.create_sgen(
    net,
    bus=bus_industrial,
    p_mw=pv_power,
    q_mvar=0.0,
    name="Solar PV"
)

print(f"Selected Simulation Hour: {SIMULATION_HOUR}:00")
print(f"PV Generation at selected hour: {pv_power:.2f} MW")
print(f"Industrial Load at selected hour: {industrial_load_demand:.2f} MW")

# ============================================================
# 11.1 BATTERY PARAMETERS
# ============================================================

battery_capacity_mwh = 0.50
battery_initial_soc = 70.0
battery_min_soc = 20.0
battery_max_soc = 90.0
battery_min_energy_mwh = battery_capacity_mwh * battery_min_soc / 100.0
battery_max_energy_mwh = battery_capacity_mwh * battery_max_soc / 100.0
battery_max_power_mw = 0.15
battery_charge_efficiency = 0.95
battery_discharge_efficiency = 0.95

battery_energy_mwh = battery_capacity_mwh * battery_initial_soc / 100.0

battery_history = []
selected_battery_power = 0.0
selected_battery_status = "IDLE"
selected_battery_soc = battery_initial_soc
selected_renewable_balance = 0.0

for i, hour in enumerate(simulation_hours):

    if i < len(simulation_hours) - 1:
        timestep_hours = simulation_hours[i + 1] - simulation_hours[i]
    else:
        timestep_hours = 1.0

    current_pv = float(pv_profile[i])
    current_load = float(industrial_load_profile[i])
    renewable_balance = current_pv - current_load

    soc_start = battery_energy_mwh / battery_capacity_mwh * 100.0

    battery_power_this_step = 0.0
    battery_status_this_step = "IDLE"

    if BATTERY_MODE == "auto":

        if renewable_balance > 0:
            available_surplus_mw = renewable_balance
            available_soc_space_mwh = battery_max_energy_mwh - battery_energy_mwh
            soc_limited_charge_power = (
                available_soc_space_mwh /
                (timestep_hours * battery_charge_efficiency)
            )

            charge_power = min(
                available_surplus_mw,
                battery_max_power_mw,
                soc_limited_charge_power
            )

            if charge_power > 1e-9:
                battery_power_this_step = charge_power
                battery_status_this_step = "CHARGING"

        elif renewable_balance < 0:
            required_power_mw = abs(renewable_balance)
            available_energy_mwh = battery_energy_mwh - battery_min_energy_mwh
            soc_limited_discharge_power = (
                available_energy_mwh * battery_discharge_efficiency /
                timestep_hours
            )

            discharge_power = min(
                required_power_mw,
                battery_max_power_mw,
                max(0.0, soc_limited_discharge_power)
            )

            if discharge_power > 1e-9:
                battery_power_this_step = -discharge_power
                battery_status_this_step = "DISCHARGING"

    elif BATTERY_MODE == "idle":
        battery_power_this_step = 0.0
        battery_status_this_step = "IDLE"

    else:
        raise ValueError("Invalid BATTERY_MODE. Use 'auto' or 'idle'.")

    if battery_power_this_step > 0:
        battery_energy_mwh += (
            battery_power_this_step * timestep_hours * battery_charge_efficiency
        )
    elif battery_power_this_step < 0:
        battery_energy_mwh -= (
            abs(battery_power_this_step) * timestep_hours / battery_discharge_efficiency
        )

    battery_energy_mwh = min(battery_energy_mwh, battery_max_energy_mwh)
    battery_energy_mwh = max(battery_energy_mwh, battery_min_energy_mwh)

    soc_end = battery_energy_mwh / battery_capacity_mwh * 100.0

    battery_history.append({
        "Time": f"{int(hour):02d}:00",
        "PV_MW": current_pv,
        "Load_MW": current_load,
        "Surplus_Deficit_MW": renewable_balance,
        "Battery_Power_MW": battery_power_this_step,
        "Battery_Status": battery_status_this_step,
        "SOC_Start_%": soc_start,
        "SOC_End_%": soc_end
    })

    if hour == SIMULATION_HOUR:
        selected_battery_power = battery_power_this_step
        selected_battery_status = battery_status_this_step
        selected_battery_soc = soc_end
        selected_renewable_balance = renewable_balance

battery_history_df = pd.DataFrame(battery_history)

battery_power = selected_battery_power
battery_status = selected_battery_status
battery_soc = selected_battery_soc
renewable_surplus = selected_renewable_balance

battery_storage = pp.create_storage(
    net,
    bus=bus_industrial,
    p_mw=battery_power,
    q_mvar=0.0,
    max_e_mwh=battery_capacity_mwh,
    soc_percent=battery_soc,
    min_e_mwh=battery_min_energy_mwh,
    name="Battery Storage"
)

print("\n------------------------------------------------------------")
print("DYNAMIC BATTERY SOC HISTORY")
print("------------------------------------------------------------")
print(
    battery_history_df[
        [
            "Time", "PV_MW", "Load_MW", "Surplus_Deficit_MW",
            "Battery_Power_MW", "Battery_Status", "SOC_End_%"
        ]
    ].round(3).to_string(index=False)
)

print("\n------------------------------------------------------------")
print("SELECTED BATTERY OPERATING POINT")
print("------------------------------------------------------------")
print(f"Renewable Surplus/Deficit: {renewable_surplus:+.2f} MW")
print(f"Battery Power: {abs(battery_power):.2f} MW")
print(f"Battery Status: {battery_status}")
print(f"Battery SOC at selected hour: {battery_soc:.2f}%")
print(f"Initial Battery SOC: {battery_initial_soc:.2f}%")
print(f"Battery Minimum SOC: {battery_min_soc:.2f}%")
print(f"Battery Maximum SOC: {battery_max_soc:.2f}%")
print(
    f"Dynamic Simulation Final SOC: "
    f"{battery_history_df.iloc[-1]['SOC_End_%']:.2f}%"
)
print("\nBattery sign convention: positive = charging, negative = discharging.")
print("\nDynamic battery simulation completed successfully.")

# ============================================================
# STEP 13 - NETWORK INFORMATION
# ============================================================

print("\n===== NETWORK CREATED =====")

print("\nBuses:")

print(
    net.bus[
        ["name", "vn_kv"]
    ]
)


print("\nLines:")

print(
    net.line[
        [
            "name",
            "length_km",
            "max_i_ka"
        ]
    ]
)


print("\nTransformers:")

print(
    net.trafo[
        [
            "name",
            "sn_mva",
            "vn_hv_kv",
            "vn_lv_kv"
        ]
    ]
)


print("\nLoads:")

print(
    net.load[
        [
            "name",
            "p_mw",
            "q_mvar"
        ]
    ]
)


# ============================================================
# STEP 14 - NETWORKX RESTORATION PATH ANALYSIS
# ============================================================

networkx_paths = find_restoration_paths()


print("\n===== NETWORKX RESTORATION PATHS =====")

for path in networkx_paths:

    print(
        " -> ".join(path)
    )


# ============================================================
# STEP 15 - CONVERT NETWORKX PATHS
#          INTO RESTORATION CANDIDATES
# ============================================================

backup_candidates = []


for path in networkx_paths:

    # --------------------------------------------------------
    # Candidate 1 - Normal backup path
    # --------------------------------------------------------

    if (
        "Backup LV Bus" in path
        and "Alternative Backup Bus" not in path
    ):

        backup_candidates.append(
            {
                "tie_switch":
                    "Normally Open Tie Switch",

                "feeder":
                    "Backup LV Feeder",

                "feeder_index":
                    backup_lv_line
            }
        )


    # --------------------------------------------------------
    # Candidate 2 - Alternative backup path
    # --------------------------------------------------------

    elif (
        "Alternative Backup Bus" in path
    ):

        backup_candidates.append(
            {
                "tie_switch":
                    "Alternative Tie Switch",

                "feeder":
                    "Alternative Backup Feeder",

                "feeder_index":
                    alternative_backup_line
            }
        )


print(
    "\n===== BACKUP RESTORATION OPTIONS ====="
)


for candidate in backup_candidates:

    print(
        "Tie Switch:",
        candidate["tie_switch"],
        "| Feeder:",
        candidate["feeder"]
    )


# ============================================================
# STEP 16 - PROTECTION RELAY SETTINGS
# ============================================================

relay_pickup_current_ka = 0.90


print(
    "\n===== RELAY SETTINGS ====="
)

print(
    f"Relay Pickup Current: "
    f"{relay_pickup_current_ka:.2f} kA"
)


# ============================================================
# STEP 17 - MULTI-TIME-STEP POWER FLOW
# ============================================================

print("\n============================================================")
print("STEP 17 - MULTI-TIME-STEP POWER FLOW SIMULATION")
print("============================================================")

power_flow_history = []

for i, hour in enumerate(simulation_hours):

    current_pv = float(pv_profile[i])
    current_load = float(industrial_load_profile[i])
    current_battery_power = float(
        battery_history_df.iloc[i]["Battery_Power_MW"]
    )
    current_battery_soc = float(
        battery_history_df.iloc[i]["SOC_End_%"]
    )

    net.sgen.at[pv_system, "p_mw"] = current_pv
    net.load.at[industrial_load, "p_mw"] = current_load
    net.storage.at[battery_storage, "p_mw"] = current_battery_power
    net.storage.at[battery_storage, "soc_percent"] = current_battery_soc

    try:
        pp.runpp(net, algorithm="nr", numba=False)
        pf_converged = bool(net.converged)
    except Exception:
        pf_converged = False

    if pf_converged:
        industrial_voltage = float(
            net.res_bus.at[bus_industrial, "vm_pu"]
        )
        minimum_bus_voltage = float(
            net.res_bus["vm_pu"].min()
        )
        industrial_current = abs(
            net.res_line.at[industrial_line, "i_from_ka"]
        )
        industrial_feeder_loading = float(
            net.res_line.at[industrial_line, "loading_percent"]
        )
        main_transformer_loading = float(
            net.res_trafo.at[main_trafo, "loading_percent"]
        )
        backup_transformer_loading = float(
            net.res_trafo.at[backup_trafo, "loading_percent"]
        )
        line_losses_mw = float(net.res_line["pl_mw"].sum())
        transformer_losses_mw = float(net.res_trafo["pl_mw"].sum())
        total_losses_mw = line_losses_mw + transformer_losses_mw
    else:
        industrial_voltage = np.nan
        minimum_bus_voltage = np.nan
        industrial_current = np.nan
        industrial_feeder_loading = np.nan
        main_transformer_loading = np.nan
        backup_transformer_loading = np.nan
        total_losses_mw = np.nan

    power_flow_history.append({
        "Time": f"{int(hour):02d}:00",
        "PV_MW": current_pv,
        "Load_MW": current_load,
        "Battery_Power_MW": current_battery_power,
        "Battery_SOC_%": current_battery_soc,
        "Industrial_Voltage_pu": industrial_voltage,
        "Minimum_Bus_Voltage_pu": minimum_bus_voltage,
        "Industrial_Current_kA": industrial_current,
        "Industrial_Feeder_Loading_%": industrial_feeder_loading,
        "Main_Transformer_Loading_%": main_transformer_loading,
        "Backup_Transformer_Loading_%": backup_transformer_loading,
        "Total_Losses_MW": total_losses_mw,
        "Power_Flow_Converged": pf_converged
    })

power_flow_history_df = pd.DataFrame(power_flow_history)

print("\n------------------------------------------------------------")
print("MULTI-TIME-STEP POWER FLOW RESULTS")
print("------------------------------------------------------------")
print(
    power_flow_history_df[
        [
            "Time", "PV_MW", "Load_MW", "Battery_Power_MW",
            "Battery_SOC_%", "Industrial_Voltage_pu",
            "Industrial_Feeder_Loading_%",
            "Main_Transformer_Loading_%", "Total_Losses_MW",
            "Power_Flow_Converged"
        ]
    ].round(3).to_string(index=False)
)

# Restore the selected 12:00 operating point for the FDIR simulation.
selected_index = np.where(
    simulation_hours == SIMULATION_HOUR
)[0][0]

net.sgen.at[pv_system, "p_mw"] = float(pv_profile[selected_index])
net.load.at[industrial_load, "p_mw"] = float(
    industrial_load_profile[selected_index]
)
net.storage.at[battery_storage, "p_mw"] = float(
    battery_history_df.iloc[selected_index]["Battery_Power_MW"]
)
net.storage.at[battery_storage, "soc_percent"] = float(
    battery_history_df.iloc[selected_index]["SOC_End_%"]
)

pp.runpp(net, algorithm="nr", numba=False)

normal_industrial_current = abs(
    net.res_line.at[industrial_line, "i_from_ka"]
)

print("\n===== NORMAL RELAY MEASUREMENT =====")
print(
    f"Industrial Feeder Current: "
    f"{normal_industrial_current:.3f} kA"
)
print(f"Operating Point: {SIMULATION_HOUR}:00")
print(
    f"Industrial Bus Voltage: "
    f"{net.res_bus.at[bus_industrial, 'vm_pu']:.3f} pu"
)
print(
    f"Industrial Feeder Loading: "
    f"{net.res_line.at[industrial_line, 'loading_percent']:.2f}%"
)
print("\nMulti-time-step power-flow simulation completed successfully.")

# ============================================================
# STEP 18 - FAULT / ABNORMAL CONDITION
# ============================================================

print(
    "\n===== FAULT SIMULATION ====="
)


if SCENARIO == "overcurrent":

    # Increase industrial load.

    net.load.at[
        industrial_load,
        "p_mw"
    ] = 0.80

    net.load.at[
        industrial_load,
        "q_mvar"
    ] = 0.30


    print(
        "Abnormal overcurrent condition "
        "created on Industrial Feeder."
    )


elif SCENARIO == "feeder_outage":

    # Simulate physical feeder outage.

    net.switch.at[
        industrial_breaker,
        "closed"
    ] = False

    net.line.at[
        industrial_line,
        "in_service"
    ] = False


    print(
        "Industrial Feeder outage simulated."
    )


elif SCENARIO == "normal":

    print(
        "No fault condition applied. "
        "Network operating normally."
    )


else:

    raise ValueError(
        "Invalid SCENARIO. Use "
        "'overcurrent', "
        "'feeder_outage', "
        "or 'normal'."
    )


# ============================================================
# STEP 19 - POWER FLOW DURING FAULT
# ============================================================

pp.runpp(
    net,
    algorithm="nr",
    numba=False
)


if SCENARIO == "feeder_outage":

    fault_current = None

    print(
        "Industrial Feeder Fault Current: "
        "Not applicable (feeder outage)"
    )


elif SCENARIO == "overcurrent":

    fault_current = abs(
        net.res_line.at[
            industrial_line,
            "i_from_ka"
        ]
    )

    print(
        f"Industrial Feeder Fault Current: "
        f"{fault_current:.3f} kA"
    )

else:

    fault_current = None

    print(
        "Industrial Feeder Fault Current: "
        "Not applicable (normal operation)"
    )


# ============================================================
# STEP 20 - FAULT DETECTION
# ============================================================

print(
    "\n===== RELAY FAULT DETECTION ====="
)


fault_detected = False

restoration_required = False

restoration_successful = False
restored_voltage = None
restored_feeder_loading = None
restored_transformer_loading = None
selected_tie_switch = None
selected_backup_feeder = None


# ------------------------------------------------------------
# OVERCURRENT
# ------------------------------------------------------------

if SCENARIO == "overcurrent":

    if fault_current > relay_pickup_current_ka:

        fault_detected = True

        restoration_required = True


        print(
            "OVERCURRENT DETECTED."
        )

        print(
            "RELAY OPERATED."
        )


        net.switch.at[
            industrial_breaker,
            "closed"
        ] = False


        net.line.at[
            industrial_line,
            "in_service"
        ] = False


        print(
            "INDUSTRIAL FEEDER BREAKER TRIPPED."
        )

        print(
            "INDUSTRIAL FEEDER ISOLATED."
        )

        print(
            "RESTORATION REQUIRED: "
            "Switching industrial load "
            "to backup supply."
        )


    else:

        print(
            "NO OVERCURRENT DETECTED."
        )

        print(
            "Protection system remains "
            "in normal operation."
        )


# ------------------------------------------------------------
# FEEDER OUTAGE
# ------------------------------------------------------------

elif SCENARIO == "feeder_outage":

    fault_detected = True

    restoration_required = True


    print(
        "FEEDER OUTAGE DETECTED."
    )

    print(
        "INDUSTRIAL FEEDER ALREADY ISOLATED."
    )

    print(
        "RESTORATION REQUIRED: "
        "Switching industrial load "
        "to backup supply."
    )


# ------------------------------------------------------------
# NORMAL
# ------------------------------------------------------------

elif SCENARIO == "normal":

    print(
        "NO FAULT DETECTED."
    )

    print(
        "Protection system remains "
        "in normal operation."
    )


# ============================================================
# STEP 21 - FDIR RESTORATION CONTROLLER
# ============================================================

feasible_candidates = []

selected_candidate = None


# ============================================================
# CHECK WHETHER RESTORATION IS REQUIRED
# ============================================================

if restoration_required:

    # ========================================================
    # STEP 21A - TEST RESTORATION CANDIDATES
    # ========================================================

    print(
        "\n===== TESTING BACKUP "
        "RESTORATION CANDIDATES ====="
    )


    for candidate in backup_candidates:

        print(
            "\nTesting:",
            candidate["tie_switch"]
        )


        # ----------------------------------------------------
        # Open both tie switches
        # ----------------------------------------------------

        net.switch.at[
            normal_tie_switch,
            "closed"
        ] = False

        net.switch.at[
            alternative_tie_switch,
            "closed"
        ] = False


        # ----------------------------------------------------
        # Identify candidate switch
        # ----------------------------------------------------

        if (
            candidate["tie_switch"]
            == "Normally Open Tie Switch"
        ):

            selected_switch_index = (
                normal_tie_switch
            )


        elif (
            candidate["tie_switch"]
            == "Alternative Tie Switch"
        ):

            selected_switch_index = (
                alternative_tie_switch
            )


        else:

            print(
                "Unknown tie switch."
            )

            continue


        # ----------------------------------------------------
        # Close candidate switch
        # ----------------------------------------------------

        net.switch.at[
            selected_switch_index,
            "closed"
        ] = True


        # ----------------------------------------------------
        # Run power flow
        # ----------------------------------------------------

        try:

            pp.runpp(
                net,
                algorithm="nr",
                numba=False
            )

            converged = net.converged


        except Exception:

            converged = False


        # ----------------------------------------------------
        # Evaluate candidate
        # ----------------------------------------------------

        if converged:

            industrial_voltage = (
                net.res_bus.at[
                    bus_industrial,
                    "vm_pu"
                ]
            )


            feeder_loading = (
                net.res_line.at[
                    candidate["feeder_index"],
                    "loading_percent"
                ]
            )


            backup_transformer_loading = (
                net.res_trafo.at[
                    backup_trafo,
                    "loading_percent"
                ]
            )


            print(
                f"Industrial Bus Voltage: "
                f"{industrial_voltage:.3f} pu"
            )


            print(
                f"Backup Feeder Loading: "
                f"{feeder_loading:.2f}%"
            )


            print(
                f"Backup Transformer Loading: "
                f"{backup_transformer_loading:.2f}%"
            )


            # ------------------------------------------------
            # RESTORATION CONSTRAINTS
            # ------------------------------------------------

            voltage_ok = (
                industrial_voltage >= 0.95
            )


            feeder_ok = (
                feeder_loading <= 100
            )


            transformer_ok = (
                backup_transformer_loading <= 100
            )


            # ------------------------------------------------
            # CANDIDATE DECISION
            # ------------------------------------------------

            if (
                voltage_ok
                and feeder_ok
                and transformer_ok
            ):

                print(
                    "RESULT: FEASIBLE"
                )


                feasible_candidates.append(
                    {
                        "tie_switch":
                            candidate["tie_switch"],

                        "feeder":
                            candidate["feeder"],

                        "feeder_index":
                            candidate["feeder_index"],

                        "industrial_voltage":
                            industrial_voltage,

                        "feeder_loading":
                            feeder_loading,

                        "transformer_loading":
                            backup_transformer_loading
                    }
                )


            else:

                print(
                    "RESULT: NOT FEASIBLE"
                )


        else:

            print(
                "RESULT: POWER FLOW "
                "DID NOT CONVERGE"
            )


        # ----------------------------------------------------
        # Open candidate before next test
        # ----------------------------------------------------

        net.switch.at[
            selected_switch_index,
            "closed"
        ] = False


    # ========================================================
    # STEP 22 - AUTOMATIC RESTORATION SELECTION
    # ========================================================

    print(
        "\n===== AUTOMATIC "
        "RESTORATION SELECTION ====="
    )


    if feasible_candidates:

        # Select the candidate with
        # minimum feeder loading.

        selected_candidate = min(
            feasible_candidates,
            key=lambda x: x["feeder_loading"]
        )

        selected_tie_switch = selected_candidate["tie_switch"]
        selected_backup_feeder = selected_candidate["feeder"]


        print(
            "Selected Tie Switch:",
            selected_candidate["tie_switch"]
        )


        print(
            "Selected Feeder:",
            selected_candidate["feeder"]
        )


        print(
            f"Feeder Loading: "
            f"{selected_candidate['feeder_loading']:.2f}%"
        )


    else:

        print(
            "NO FEASIBLE RESTORATION "
            "PATH FOUND."
        )


    # ========================================================
    # STEP 23 - AUTOMATIC RESTORATION OPERATION
    # ========================================================

    if selected_candidate is not None:

        print(
            "\n===== RESTORATION OPERATION ====="
        )


        # Keep both tie switches open first.

        net.switch.at[
            normal_tie_switch,
            "closed"
        ] = False


        net.switch.at[
            alternative_tie_switch,
            "closed"
        ] = False


        # ----------------------------------------------------
        # Close selected tie switch
        # ----------------------------------------------------

        if (
            selected_candidate["tie_switch"]
            == "Normally Open Tie Switch"
        ):

            net.switch.at[
                normal_tie_switch,
                "closed"
            ] = True


        elif (
            selected_candidate["tie_switch"]
            == "Alternative Tie Switch"
        ):

            net.switch.at[
                alternative_tie_switch,
                "closed"
            ] = True


        print(
            "SELECTED TIE SWITCH CLOSED:",
            selected_candidate["tie_switch"]
        )


        print(
            "BACKUP SUPPLY CONNECTED."
        )


        # ====================================================
        # STEP 24 - RESTORATION VERIFICATION
        # ====================================================

        print(
            "\n===== RESTORATION CHECK ====="
        )


        pp.runpp(
            net,
            algorithm="nr",
            numba=False
        )


        restored_voltage = (
            net.res_bus.at[
                bus_industrial,
                "vm_pu"
            ]
        )


        restored_feeder_loading = (
            net.res_line.at[
                selected_candidate["feeder_index"],
                "loading_percent"
            ]
        )


        restored_transformer_loading = (
            net.res_trafo.at[
                backup_trafo,
                "loading_percent"
            ]
        )


        print(
            f"Industrial Bus Voltage: "
            f"{restored_voltage:.3f} pu"
        )


        print(
            f"Selected Backup Feeder Loading: "
            f"{restored_feeder_loading:.2f}%"
        )


        print(
            f"Backup Transformer Loading: "
            f"{restored_transformer_loading:.2f}%"
        )


        # ----------------------------------------------------
        # FINAL RESTORATION CONSTRAINTS
        # ----------------------------------------------------

        final_voltage_ok = (
            restored_voltage >= 0.95
        )


        final_feeder_ok = (
            restored_feeder_loading <= 100
        )


        final_transformer_ok = (
            restored_transformer_loading <= 100
        )


        if (
            final_voltage_ok
            and final_feeder_ok
            and final_transformer_ok
        ):

            restoration_successful = True


            print(
                "\nRESTORATION SUCCESSFUL"
            )


            print(
                "All restoration constraints "
                "satisfied."
            )


        else:

            restoration_successful = False


            print(
                "\nRESTORATION FAILED"
            )


            print(
                "One or more restoration "
                "constraints were violated."
            )


    else:

        restoration_successful = False


        print(
            "\nRESTORATION NOT COMPLETED."
        )


# ============================================================
# NO RESTORATION REQUIRED
# ============================================================

else:

    restoration_successful = False


    print(
        "\n===== RESTORATION NOT REQUIRED ====="
    )


    print(
        "No fault detected."
    )


    print(
        "Network remains in normal "
        "operating condition."
    )


# ============================================================
# STEP 25 - FINAL NETWORK RESULTS
# ============================================================

print(
    "\n======================================================"
)

print(
    " FINAL DIGITAL TWIN NETWORK RESULTS"
)

print(
    "======================================================"
)


# ------------------------------------------------------------
# BUS VOLTAGES
# ------------------------------------------------------------

print(
    "\n===== BUS VOLTAGES ====="
)


print(
    net.res_bus[
        [
            "vm_pu",
            "va_degree"
        ]
    ]
)


# ------------------------------------------------------------
# LINE RESULTS
# ------------------------------------------------------------

print(
    "\n===== LINE RESULTS ====="
)


print(
    net.res_line[
        [
            "loading_percent",
            "i_from_ka",
            "i_to_ka"
        ]
    ]
)


# ------------------------------------------------------------
# TRANSFORMER RESULTS
# ------------------------------------------------------------

print(
    "\n===== TRANSFORMER RESULTS ====="
)


print(
    net.res_trafo[
        [
            "loading_percent",
            "i_hv_ka",
            "i_lv_ka"
        ]
    ]
)


# ------------------------------------------------------------
# SWITCH STATUS
# ------------------------------------------------------------

print(
    "\n===== SWITCH STATUS ====="
)


print(
    net.switch[
        [
            "name",
            "closed"
        ]
    ]
)


# ------------------------------------------------------------
# POWER FLOW STATUS
# ------------------------------------------------------------

print(
    "\n===== POWER FLOW STATUS ====="
)


print(
    "Power Flow Converged:",
    net.converged
)


# ============================================================
# STEP 26 - ENERGY MANAGEMENT SUMMARY
# ============================================================

print(
    "\n======================================================"
)

print(
    " ENERGY MANAGEMENT SUMMARY"
)

print(
    "======================================================"
)


print(
    f"Solar PV Generation: "
    f"{pv_power:.2f} MW"
)


print(
    f"Industrial Load Demand: "
    f"{industrial_load_demand:.2f} MW"
)


print(
    f"PV Surplus/Deficit: "
    f"{renewable_surplus:.2f} MW"
)


print(
    f"Battery SOC: "
    f"{battery_soc:.1f}%"
)


print(
    f"Battery Power: "
    f"{abs(battery_power):.2f} MW"
)


print(
    f"Battery Operating State: "
    f"{battery_status}"
)


# ============================================================
# STEP 27 - FINAL FDIR SUMMARY
# ============================================================

print(
    "\n======================================================"
)

print(
    " FDIR SUMMARY"
)

print(
    "======================================================"
)


if fault_detected:

    print(
        "1. Fault/abnormal condition detected"
    )


    if SCENARIO == "overcurrent":

        print(
            "2. Relay evaluated feeder current"
        )

        print(
            "3. Industrial feeder breaker operated"
        )


    elif SCENARIO == "feeder_outage":

        print(
            "2. Feeder outage condition identified"
        )

        print(
            "3. Industrial feeder already isolated"
        )


    print(
        "4. Faulted feeder isolated"
    )


    if selected_candidate is not None:

        print(
            "5. Restoration path evaluated "
            "using NetworkX + power flow"
        )


        print(
            "6. Feasible backup path "
            "selected automatically"
        )


        print(
            "7. Industrial load restored "
            "through backup supply"
        )


        print(
            "8. Voltage and loading "
            "constraints verified"
        )


    else:

        print(
            "5. No feasible restoration "
            "path available"
        )


else:

    print(
        "1. No fault detected"
    )


    print(
        "2. Protection system remained "
        "in normal operation"
    )


    print(
        "3. No feeder isolation required"
    )


    print(
        "4. No restoration required"
    )


# ============================================================
# SIMULATION COMPLETE
# ============================================================

print(
    "\n======================================================"
)

print(
    " SIMULATION COMPLETE"
)

print(
    "======================================================\n"
)


# ============================================================
# DASHBOARD SCENARIO RESULT EXPORT
# ============================================================

# ------------------------------------------------------------
# PROTECTION STATUS
# ------------------------------------------------------------

relay_tripped = False
breaker_open = False

if SCENARIO == "overcurrent" and fault_detected:
    relay_tripped = True
    breaker_open = not bool(
        net.switch.at[industrial_breaker, "closed"]
    )

elif SCENARIO == "feeder_outage" and fault_detected:
    # Feeder outage is an equipment/outage condition.
    # The breaker is used to isolate the feeder, but the
    # virtual overcurrent relay is not claimed to have operated.
    relay_tripped = False
    breaker_open = not bool(
        net.switch.at[industrial_breaker, "closed"]
    )

else:
    relay_tripped = False
    breaker_open = not bool(
        net.switch.at[industrial_breaker, "closed"]
    )


# ------------------------------------------------------------
# FAULT DESCRIPTION
# ------------------------------------------------------------

if SCENARIO == "overcurrent":
    fault_type = "Overcurrent Fault"
    faulted_element = "Industrial Feeder"

elif SCENARIO == "feeder_outage":
    fault_type = "Feeder Outage"
    faulted_element = "Industrial Feeder"

else:
    fault_type = "No Fault"
    faulted_element = "None"


# ------------------------------------------------------------
# ACTIVE POWER-FLOW PATH
# ------------------------------------------------------------

if not fault_detected:

    active_power_flow_path = [
        "Utility Grid",
        "Main 11kV Line",
        "Main Transformer",
        "Industrial Feeder",
        "Industrial Bus",
        "Industrial Load"
    ]

elif restoration_successful:

    if selected_tie_switch == "Alternative Tie Switch":

        active_power_flow_path = [
            "Utility Grid",
            "Backup 11kV Line",
            "Backup Transformer",
            "Backup LV Bus",
            "Alternative Backup Feeder",
            "Alternative Tie Switch",
            "Industrial Bus",
            "Industrial Load"
        ]

    else:

        active_power_flow_path = [
            "Utility Grid",
            "Backup 11kV Line",
            "Backup Transformer",
            "Backup LV Bus",
            "Backup LV Feeder",
            "Normally Open Tie Switch",
            "Industrial Bus",
            "Industrial Load"
        ]

else:

    active_power_flow_path = [
        "Utility Grid",
        "Main Feeder",
        "Main Transformer",
        "Industrial Feeder",
        "Industrial Bus"
    ]


# ------------------------------------------------------------
# SWITCH STATUS
# ------------------------------------------------------------

industrial_breaker_status = bool(
    net.switch.at[industrial_breaker, "closed"]
)

normal_tie_status = bool(
    net.switch.at[normal_tie_switch, "closed"]
)

alternative_tie_status = bool(
    net.switch.at[alternative_tie_switch, "closed"]
)


# ------------------------------------------------------------
# FDIR EVENT TIMELINE
# ------------------------------------------------------------

event_timeline = []

if not fault_detected:

    event_timeline = [
        "Normal operating condition confirmed",
        "Relay monitoring active",
        "Industrial feeder breaker CLOSED",
        "No feeder isolation required",
        "No restoration required"
    ]

else:

    event_timeline.append("Fault / abnormal condition detected")

    if SCENARIO == "overcurrent":

        event_timeline.append(
            f"Industrial feeder current = "
            f"{fault_current:.3f} kA"
        )

        event_timeline.append(
            f"Relay pickup = "
            f"{relay_pickup_current_ka:.2f} kA"
        )

        if relay_tripped:
            event_timeline.append(
                "Virtual overcurrent relay TRIPPED"
            )

        if breaker_open:
            event_timeline.append(
                "Industrial feeder circuit breaker OPEN"
            )

    elif SCENARIO == "feeder_outage":

        event_timeline.append(
            "Industrial feeder outage identified"
        )

        event_timeline.append(
            "Industrial feeder isolated"
        )

    event_timeline.append(
        "NetworkX searched for alternate restoration paths"
    )

    event_timeline.append(
        "Power-flow constraints evaluated"
    )

    if selected_candidate is not None:

        event_timeline.append(
            f"Selected {selected_tie_switch}"
        )

        event_timeline.append(
            f"{selected_tie_switch} CLOSED"
        )

        if restoration_successful:

            event_timeline.append(
                "Industrial load restored through backup supply"
            )

            event_timeline.append(
                "Voltage and loading constraints verified"
            )

            event_timeline.append(
                "RESTORATION SUCCESSFUL"
            )

        else:

            event_timeline.append(
                "RESTORATION FAILED"
            )

    else:

        event_timeline.append(
            "No feasible restoration path available"
        )


# ------------------------------------------------------------
# DASHBOARD JSON
# ------------------------------------------------------------

dashboard_result = {

    "scenario": SCENARIO,

    "fault_type": fault_type,

    "faulted_element": faulted_element,

    "fault_detected": bool(fault_detected),

    "restoration_required": bool(
        restoration_required
    ),

    "restoration_successful": bool(
        restoration_successful
    ),

    # Protection
    "relay_pickup_current_ka": float(
        relay_pickup_current_ka
    ),

    "normal_industrial_current_ka": float(
        normal_industrial_current
    ),

    "fault_current_ka": (
        None
        if fault_current is None
        else float(fault_current)
    ),

    "relay_tripped": bool(
        relay_tripped
    ),

    "breaker_open": bool(
        breaker_open
    ),

    "industrial_breaker_closed": bool(
        industrial_breaker_status
    ),

    # Tie switches
    "normal_tie_switch_closed": bool(
        normal_tie_status
    ),

    "alternative_tie_switch_closed": bool(
        alternative_tie_status
    ),

    "selected_tie_switch": (
        selected_tie_switch
    ),

    "selected_backup_feeder": (
        selected_backup_feeder
    ),

    # Restoration
    "restored_voltage_pu": (
        None
        if restored_voltage is None
        else float(restored_voltage)
    ),

    "restored_feeder_loading_percent": (
        None
        if restored_feeder_loading is None
        else float(restored_feeder_loading)
    ),

    "restored_transformer_loading_percent": (
        None
        if restored_transformer_loading is None
        else float(restored_transformer_loading)
    ),

    # Power flow
    "active_power_flow_path": (
        active_power_flow_path
    ),

    # FDIR timeline
    "event_timeline": event_timeline
}


with open(
    "dashboard_scenario_results.json",
    "w"
) as file:

    json.dump(
        dashboard_result,
        file,
        indent=4
    )


print()
print(
    "Dashboard scenario result saved to: "
    "dashboard_scenario_results.json"
)

# ============================================================
# STEP 18 - STAGE 6: PERFORMANCE METRICS & GRAPHS
# ============================================================

print()
print("=" * 70)
print("STEP 18 - STAGE 6: PERFORMANCE METRICS & GRAPHS")
print("=" * 70)

stage6_df = power_flow_history_df.copy()

# ------------------------------------------------------------
# 18.1 PERFORMANCE METRICS
# ------------------------------------------------------------

minimum_industrial_voltage = stage6_df["Industrial_Voltage_pu"].min()
maximum_industrial_voltage = stage6_df["Industrial_Voltage_pu"].max()
maximum_industrial_feeder_loading = stage6_df["Industrial_Feeder_Loading_%"].max()
maximum_main_transformer_loading = stage6_df["Main_Transformer_Loading_%"].max()
maximum_backup_transformer_loading = stage6_df["Backup_Transformer_Loading_%"].max()

# Energy estimates using trapezoidal integration over the
# simulated time points.
stage6_df["Time_Hours"] = stage6_df["Time"].apply(
    lambda x: int(str(x).split(":")[0])
    + int(str(x).split(":")[1]) / 60.0
)

_time_axis = stage6_df["Time_Hours"].to_numpy(dtype=float)
total_energy_losses_mwh = float(
    np.trapezoid(
        stage6_df["Total_Losses_MW"].fillna(0.0).to_numpy(dtype=float),
        _time_axis
    )
)
pv_energy_mwh = float(
    np.trapezoid(
        stage6_df["PV_MW"].to_numpy(dtype=float),
        _time_axis
    )
)
load_energy_mwh = float(
    np.trapezoid(
        stage6_df["Load_MW"].to_numpy(dtype=float),
        _time_axis
    )
)

renewable_utilization_percent = (
    (pv_energy_mwh / load_energy_mwh) * 100
    if load_energy_mwh > 0
    else 0.0
)

restoration_voltage_pu = float(net.res_bus.vm_pu.at[bus_industrial])

selected_backup_loading = None
if selected_candidate is not None:
    try:
        selected_backup_loading = float(
            net.res_line.loading_percent.at[
                selected_candidate["feeder_index"]
            ]
        )
    except Exception:
        selected_backup_loading = None

print()
print("------------------------------------------------------------")
print("STAGE 6 PERFORMANCE METRICS")
print("------------------------------------------------------------")
print(f"Minimum Industrial Bus Voltage: {minimum_industrial_voltage:.3f} pu")
print(f"Maximum Industrial Bus Voltage: {maximum_industrial_voltage:.3f} pu")
print(
    f"Maximum Industrial Feeder Loading: "
    f"{maximum_industrial_feeder_loading:.2f}%"
)
print(
    f"Maximum Main Transformer Loading: "
    f"{maximum_main_transformer_loading:.2f}%"
)
print(
    f"Maximum Backup Transformer Loading: "
    f"{maximum_backup_transformer_loading:.2f}%"
)
print(f"Approx. PV Energy over Simulation: {pv_energy_mwh:.3f} MWh")
print(f"Approx. Load Energy over Simulation: {load_energy_mwh:.3f} MWh")
print(f"PV-to-Load Energy Coverage: {renewable_utilization_percent:.2f}%")
print(f"Approx. Network Energy Losses: {total_energy_losses_mwh:.3f} MWh")
print(f"Restoration Verification Voltage: {restoration_voltage_pu:.3f} pu")

if selected_backup_loading is not None:
    print(
        f"Selected Backup Feeder Loading after Restoration: "
        f"{selected_backup_loading:.2f}%"
    )

# ------------------------------------------------------------
# 18.2 PREPARE GRAPH DATA

def hour_label(hour_value):
    value = str(hour_value)
    if ":" in value:
        return value
    return f"{int(round(float(hour_value))):02d}:00"

stage6_df["Time_Label"] = stage6_df["Time"].apply(hour_label)

# ------------------------------------------------------------
# 18.3 GRAPH 1 - BATTERY SOC
# ------------------------------------------------------------

plt.figure(figsize=(9, 5))
plt.plot(
    stage6_df["Time_Label"],
    stage6_df["Battery_SOC_%"],
    marker="o",
    linewidth=2,
)
plt.axhline(
    battery_min_soc,
    linestyle="--",
    linewidth=1.5,
    label="Minimum SOC",
)
plt.axhline(
    battery_max_soc,
    linestyle="--",
    linewidth=1.5,
    label="Maximum SOC",
)
plt.xlabel("Time")
plt.ylabel("Battery SOC (%)")
plt.title("Battery State of Charge vs Time")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()

# ------------------------------------------------------------
# 18.4 GRAPH 2 - PV GENERATION AND LOAD
# ------------------------------------------------------------

plt.figure(figsize=(9, 5))
plt.plot(
    stage6_df["Time_Label"],
    stage6_df["PV_MW"],
    marker="o",
    linewidth=2,
    label="Solar PV",
)
plt.plot(
    stage6_df["Time_Label"],
    stage6_df["Load_MW"],
    marker="s",
    linewidth=2,
    label="Industrial Load",
)
plt.xlabel("Time")
plt.ylabel("Power (MW)")
plt.title("Solar PV Generation vs Industrial Load")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()

# ------------------------------------------------------------
# 18.5 GRAPH 3 - INDUSTRIAL BUS VOLTAGE
# ------------------------------------------------------------

plt.figure(figsize=(9, 5))
plt.plot(
    stage6_df["Time_Label"],
    stage6_df["Industrial_Voltage_pu"],
    marker="o",
    linewidth=2,
    label="Industrial Bus Voltage",
)
plt.axhline(
    0.95,
    linestyle="--",
    linewidth=1.5,
    label="Minimum Acceptable Voltage",
)
plt.xlabel("Time")
plt.ylabel("Voltage (pu)")
plt.title("Industrial Bus Voltage Profile")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()

# ------------------------------------------------------------
# 18.6 GRAPH 4 - FEEDER LOADING
# ------------------------------------------------------------

plt.figure(figsize=(9, 5))
plt.plot(
    stage6_df["Time_Label"],
    stage6_df["Industrial_Feeder_Loading_%"],
    marker="o",
    linewidth=2,
    label="Industrial Feeder",
)
plt.axhline(
    100,
    linestyle="--",
    linewidth=1.5,
    label="Maximum Loading Limit",
)
plt.xlabel("Time")
plt.ylabel("Loading (%)")
plt.title("Industrial Feeder Loading Profile")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()

# ------------------------------------------------------------
# 18.7 GRAPH 5 - TRANSFORMER LOADING
# ------------------------------------------------------------

plt.figure(figsize=(9, 5))
plt.plot(
    stage6_df["Time_Label"],
    stage6_df["Main_Transformer_Loading_%"],
    marker="o",
    linewidth=2,
    label="Main Transformer",
)
plt.plot(
    stage6_df["Time_Label"],
    stage6_df["Backup_Transformer_Loading_%"],
    marker="s",
    linewidth=2,
    label="Backup Transformer",
)
plt.axhline(
    100,
    linestyle="--",
    linewidth=1.5,
    label="Maximum Loading Limit",
)
plt.xlabel("Time")
plt.ylabel("Loading (%)")
plt.title("Transformer Loading Profile")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()

# ------------------------------------------------------------
# 18.8 GRAPH 6 - NETWORK LOSSES
# ------------------------------------------------------------

plt.figure(figsize=(9, 5))
plt.plot(
    stage6_df["Time_Label"],
    stage6_df["Total_Losses_MW"],
    marker="o",
    linewidth=2,
)
plt.xlabel("Time")
plt.ylabel("Power Losses (MW)")
plt.title("Network Power Losses vs Time")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# ------------------------------------------------------------
# 18.9 GRAPH 7 - BATTERY POWER
# ------------------------------------------------------------

plt.figure(figsize=(9, 5))
plt.bar(
    stage6_df["Time_Label"],
    stage6_df["Battery_Power_MW"],
)
plt.axhline(0, linewidth=1)
plt.xlabel("Time")
plt.ylabel("Battery Power (MW)")
plt.title("Battery Charging (+) / Discharging (-)")
plt.grid(True, axis="y", alpha=0.3)
plt.tight_layout()
plt.show()

# ------------------------------------------------------------
# 18.10 EXPORT STAGE 6 RESULTS
# ------------------------------------------------------------

stage6_export_columns = [
    "Time",
    "Time_Label",
    "PV_MW",
    "Load_MW",
    "Battery_Power_MW",
    "Battery_SOC_%",
    "Industrial_Voltage_pu",
    "Industrial_Feeder_Loading_%",
    "Main_Transformer_Loading_%",
    "Backup_Transformer_Loading_%",
    "Total_Losses_MW",
    "Power_Flow_Converged",
]

stage6_export_df = stage6_df[
    [c for c in stage6_export_columns if c in stage6_df.columns]
].copy()

stage6_export_path = "stage6_performance_metrics.csv"
stage6_export_df.to_csv(stage6_export_path, index=False)

print()
print("Stage 6 metrics and graphs completed successfully.")
print(f"Performance metrics saved to: {stage6_export_path}")

print()
print("=" * 70)
print("STAGE 6 COMPLETED")
print("=" * 70)

