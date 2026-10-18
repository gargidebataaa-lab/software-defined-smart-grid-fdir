import pandapower as pp

# Create an empty electrical network
net = pp.create_empty_network()

# Create two 11 kV buses
bus_grid = pp.create_bus(net, vn_kv=11, name="Grid Bus")
bus_load = pp.create_bus(net, vn_kv=11, name="Load Bus")

# Create the main electrical grid/source
pp.create_ext_grid(
    net,
    bus=bus_grid,
    vm_pu=1.0,
    name="Main Grid"
)

# Create a 1 km distribution line
pp.create_line_from_parameters(
    net,
    from_bus=bus_grid,
    to_bus=bus_load,
    length_km=1.0,
    r_ohm_per_km=0.4,
    x_ohm_per_km=0.3,
    c_nf_per_km=10,
    max_i_ka=0.4,
    name="Feeder Line 1"
)

# Create a 2 MW + 0.5 MVAr load
pp.create_load(
    net,
    bus=bus_load,
    p_mw=2.0,
    q_mvar=0.5,
    name="Industrial Load"
)

# Run Newton-Raphson power flow
pp.runpp(net, algorithm="nr")

# Display bus results
print("\n===== BUS RESULTS =====")
print(net.res_bus)

# Display line results
print("\n===== LINE RESULTS =====")
print(net.res_line)

# Check whether power flow converged
print("\n===== POWER FLOW SUCCESS =====")
print(net.converged)