import pandapower as pp
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

from networkx_engine import find_restoration_paths


# ============================================================
# SOFTWARE-DEFINED SMART GRID
# DIGITAL TWIN BASED FDIR SIMULATION
# VERSION 2
# ============================================================

print("\n======================================================")
print(" SOFTWARE-DEFINED SMART GRID")
print(" DIGITAL TWIN BASED FDIR SIMULATION")
print(" VERSION 2")
print("======================================================\n")


# ============================================================
# STEP 1 - CREATE NETWORK
# ============================================================

net = pp.create_empty_network(
    name="Digital Twin Smart Distribution Grid"
)


# ============================================================
# STEP 2 - CREATE BUSES
# ============================================================

# 11 kV buses

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


# 415 V buses

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

# Normal backup path
# Backup LV -> Backup Remote LV

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


# Alternative backup path
# Backup LV -> Alternative Backup Bus

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

# Industrial feeder circuit breaker

industrial_breaker = pp.create_switch(
    net,
    bus=bus_lv_main,
    element=industrial_line,
    et="l",
    closed=True,
    type="CB",
    name="Industrial Feeder Breaker"
)


# Normally-open tie switch

normal_tie_switch = pp.create_switch(
    net,
    bus=bus_industrial,
    element=bus_backup_remote_lv,
    et="b",
    closed=False,
    type="CB",
    name="Normally Open Tie Switch"
)


# Alternative normally-open tie switch

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
# STEP 11 - NETWORK INFORMATION
# ============================================================

print("===== NETWORK CREATED =====")

print("\nBuses:")
print(net.bus[["name", "vn_kv"]])

print("\nLines:")
print(net.line[["name", "length_km", "max_i_ka"]])

print("\nTransformers:")
print(net.trafo[["name", "sn_mva", "vn_hv_kv", "vn_lv_kv"]])

print("\nLoads:")
print(net.load[["name", "p_mw", "q_mvar"]])


# ============================================================
# STEP 12 - NETWORKX RESTORATION PATH ANALYSIS
# ============================================================

networkx_paths = find_restoration_paths()


print("\n===== NETWORKX RESTORATION PATHS =====")

for path in networkx_paths:
    print(" -> ".join(path))


# ============================================================
# STEP 13 - CONVERT NETWORKX PATHS INTO
#           RESTORATION CANDIDATES
# ============================================================

backup_candidates = []


for path in networkx_paths:

    # --------------------------------------------------------
    # Candidate 1
    # Industrial -> Backup Remote LV -> Backup LV -> Grid
    # --------------------------------------------------------

    if (
        "Backup Remote LV Bus" in path
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
    # Candidate 2
    # Industrial -> Alternative Backup -> Backup LV -> Grid
    # --------------------------------------------------------

    elif "Alternative Backup Bus" in path:

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


print("\n===== BACKUP RESTORATION OPTIONS =====")

for candidate in backup_candidates:

    print(
        "Tie Switch:",
        candidate["tie_switch"],
        "| Feeder:",
        candidate["feeder"]
    )


# ============================================================
# STEP 14 - PROTECTION RELAY SETTINGS
# ============================================================

relay_pickup_current_ka = 0.90


print("\n===== RELAY SETTINGS =====")

print(
    f"Relay Pickup Current: "
    f"{relay_pickup_current_ka:.2f} kA"
)


# ============================================================
# STEP 15 - NORMAL POWER FLOW
# ============================================================

pp.runpp(
    net,
    algorithm="nr",
    numba=False
)


normal_industrial_current = abs(
    net.res_line.at[
        industrial_line,
        "i_from_ka"
    ]
)


print("\n===== NORMAL RELAY MEASUREMENT =====")

print(
    f"Industrial Feeder Current: "
    f"{normal_industrial_current:.3f} kA"
)


# ============================================================
# STEP 16 - FAULT / ABNORMAL OVERCURRENT SIMULATION
# ============================================================

# Increase industrial load to create abnormal
# overcurrent condition.

net.load.at[
    industrial_load,
    "p_mw"
] = 0.80


net.load.at[
    industrial_load,
    "q_mvar"
] = 0.30


print("\n===== FAULT SIMULATION =====")

print(
    "Abnormal overcurrent condition created "
    "on Industrial Feeder."
)


# ============================================================
# STEP 17 - RUN POWER FLOW DURING FAULT
# ============================================================

pp.runpp(
    net,
    algorithm="nr",
    numba=False
)


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


# ============================================================
# STEP 18 - RELAY DECISION
# ============================================================

print("\n===== RELAY FAULT DETECTION =====")


if fault_current > relay_pickup_current_ka:

    print("OVERCURRENT DETECTED.")
    print("RELAY OPERATED.")


    # Trip industrial feeder breaker

    net.switch.at[
        industrial_breaker,
        "closed"
    ] = False


    # Remove faulted feeder from service.
    # This represents isolation of the faulted feeder.

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
        "Switching industrial load to backup supply."
    )

else:

    print("NO FAULT DETECTED.")

    print(
        "Protection system remains in normal operation."
    )


# ============================================================
# STEP 19 - TEST RESTORATION CANDIDATES
# ============================================================

print(
    "\n===== TESTING BACKUP RESTORATION "
    "CANDIDATES ====="
)


feasible_candidates = []


for candidate in backup_candidates:

    print(
        "\nTesting:",
        candidate["tie_switch"]
    )


    # --------------------------------------------------------
    # Ensure both tie switches are open
    # --------------------------------------------------------

    net.switch.at[
        normal_tie_switch,
        "closed"
    ] = False


    net.switch.at[
        alternative_tie_switch,
        "closed"
    ] = False


    # --------------------------------------------------------
    # Identify selected switch
    # --------------------------------------------------------

    if (
        candidate["tie_switch"]
        == "Normally Open Tie Switch"
    ):

        selected_switch_index = normal_tie_switch


    elif (
        candidate["tie_switch"]
        == "Alternative Tie Switch"
    ):

        selected_switch_index = alternative_tie_switch


    else:

        print("Unknown tie switch.")
        continue


    # --------------------------------------------------------
    # Close candidate switch
    # --------------------------------------------------------

    net.switch.at[
        selected_switch_index,
        "closed"
    ] = True


    # --------------------------------------------------------
    # Run power flow
    # --------------------------------------------------------

    try:

        pp.runpp(
            net,
            algorithm="nr",
            numba=False
        )

        converged = net.converged

    except Exception:

        converged = False


    # --------------------------------------------------------
    # If power flow converged
    # --------------------------------------------------------

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


        # ----------------------------------------------------
        # RESTORATION CONSTRAINTS
        # ----------------------------------------------------

        voltage_ok = (
            industrial_voltage >= 0.95
        )


        feeder_ok = (
            feeder_loading <= 100
        )


        transformer_ok = (
            backup_transformer_loading <= 100
        )


        # ----------------------------------------------------
        # Candidate decision
        # ----------------------------------------------------

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
            "RESULT: POWER FLOW DID NOT CONVERGE"
        )


    # --------------------------------------------------------
    # Open candidate before testing next candidate
    # --------------------------------------------------------

    net.switch.at[
        selected_switch_index,
        "closed"
    ] = False


# ============================================================
# STEP 20 - AUTOMATIC RESTORATION SELECTION
# ============================================================

print(
    "\n===== AUTOMATIC RESTORATION SELECTION ====="
)


selected_candidate = None


if feasible_candidates:

    # Select candidate with minimum feeder loading

    selected_candidate = min(
        feasible_candidates,
        key=lambda x: x["feeder_loading"]
    )


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
        "NO FEASIBLE RESTORATION PATH FOUND."
    )


# ============================================================
# STEP 21 - AUTOMATIC RESTORATION OPERATION
# ============================================================

if selected_candidate is not None:

    print(
        "\n===== RESTORATION OPERATION ====="
    )


    # Keep both tie switches open first

    net.switch.at[
        normal_tie_switch,
        "closed"
    ] = False


    net.switch.at[
        alternative_tie_switch,
        "closed"
    ] = False


    # Close selected tie switch

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


# ============================================================
# STEP 22 - RESTORATION VERIFICATION
# ============================================================

if selected_candidate is not None:

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


    # --------------------------------------------------------
    # FINAL RESTORATION CHECK
    # --------------------------------------------------------

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

        print(
            "\nRESTORATION SUCCESSFUL"
        )

        print(
            "All restoration constraints satisfied."
        )

    else:

        print(
            "\nRESTORATION FAILED"
        )

        print(
            "One or more restoration constraints "
            "were violated."
        )


# ============================================================
# STEP 23 - FINAL NETWORK RESULTS
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


print("\n===== BUS VOLTAGES =====")

print(
    net.res_bus[
        ["vm_pu", "va_degree"]
    ]
)


print("\n===== LINE RESULTS =====")

print(
    net.res_line[
        [
            "loading_percent",
            "i_from_ka",
            "i_to_ka"
        ]
    ]
)


print("\n===== TRANSFORMER RESULTS =====")

print(
    net.res_trafo[
        [
            "loading_percent",
            "i_hv_ka",
            "i_lv_ka"
        ]
    ]
)


print("\n===== SWITCH STATUS =====")

print(
    net.switch[
        [
            "name",
            "closed"
        ]
    ]
)


print("\n===== POWER FLOW STATUS =====")

print(
    "Power Flow Converged:",
    net.converged
)


# ============================================================
# STEP 24 - FINAL FDIR SUMMARY
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


print(
    "1. Fault/abnormal condition detected"
)


print(
    "2. Relay evaluated feeder current"
)


print(
    "3. Industrial feeder breaker operated"
)


print(
    "4. Faulted feeder isolated"
)


if selected_candidate is not None:

    print(
        "5. Restoration path evaluated using "
        "NetworkX + power flow"
    )

    print(
        "6. Feasible backup path selected automatically"
    )

    print(
        "7. Industrial load restored through backup supply"
    )

    print(
        "8. Voltage and loading constraints verified"
    )

else:

    print(
        "5. No feasible restoration path available"
    )


print(
    "\n======================================================"
)

print(
    " SIMULATION COMPLETE"
)

print(
    "======================================================\n"
)