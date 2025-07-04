from pickle import FALSE

from reho.model.actors_problem import *

import math

def remove_nan_QBuilding(buildings_data):
    for bui in buildings_data["buildings_data"]:
        bui_class = buildings_data["buildings_data"][bui]["id_class"]
        buildings_data["buildings_data"][bui]["id_class"] = buildings_data["buildings_data"][bui]["id_class"].replace("nan", "II")
        buildings_data["buildings_data"][bui]["id_class"] = buildings_data["buildings_data"][bui]["id_class"].replace("VIII", "III")
        buildings_data["buildings_data"][bui]["ratio"] = buildings_data["buildings_data"][bui]["ratio"].replace("nan", "0.0")
        if bui_class != buildings_data["buildings_data"][bui]["id_class"]:
            print(bui, "had nan class and was", bui_class)
        if math.isnan(buildings_data["buildings_data"][bui]["U_h"]):
            buildings_data["buildings_data"][bui]["U_h"] = 0.00181
        if math.isnan(buildings_data["buildings_data"][bui]["HeatCapacity"]):
            buildings_data["buildings_data"][bui]["HeatCapacity"] = 120
        if math.isnan(buildings_data["buildings_data"][bui]["T_comfort_min_0"]):
            buildings_data["buildings_data"][bui]["T_comfort_min_0"] = 20
    return buildings_data

if __name__ == '__main__':

    # Set building parameters
    reader = QBuildingsReader()
    reader.establish_connection('Suisse')
    qbuildings_data = reader.read_db(district_id= 9672, nb_buildings=16)
    qbuildings_data = remove_nan_QBuilding(qbuildings_data)
    #2877 egid=['1017073/1017074', '1017109', '1017079', '1030377/1030380'])

    # Select clustering options for weather data
    cluster = {'Location': 'Geneva', 'Attributes': ['T', 'I', 'W'], 'Periods': 10, 'PeriodDuration': 24}

    # Set scenario
    scenario = dict()
    scenario['Objective'] = 'TOTEX'
    scenario['EMOO'] = {}
    scenario['specific'] =[]
    #scenario['specific'] = ['EV_chargingprofile1', "EV_chargingprofile2"]
    scenario["name"] = "actors"

    # Choose energy system structure options
    scenario['exclude_units'] = [ 'Bike_district','ICE_district', 'ElectricBike_district']
    scenario['enforce_units'] = []

    # Set method options
    method = {'actors_problem': True, "refurbishment": True, "parallel_computation": True,
              "save_streams": False, "save_timeseries": False, "save_data_input": True,"print_logs": False}

    # Initialize available units and grids
    grids = infrastructure.initialize_grids({'Electricity': {"Cost_demand_cst": 0.1, "Cost_supply_cst": 0.3},
                                             'NaturalGas': {"Cost_demand_cst": 0.25, "Cost_supply_cst": 0.25},
                                             'Gasoline': {"Cost_demand_cst": 0.25, "Cost_supply_cst": 0.25},
                                             'Mobility': {"Cost_demand_cst": 0.1, "Cost_supply_cst": 5}})

    # available capacities of networks [Electricity]
    grids["Electricity"]["ReinforcementOfNetwork"] = np.array([250, 400, 630, 1000, 2000, 4000])
    grids["Mobility"]["ReinforcementOfNetwork"] = np.array([2000])
    grids["Gasoline"]["ReinforcementOfNetwork"] = np.array([2000])

    # existing capacities of networks
    Network_ext = pd.DataFrame([250, 2000, 2000, 2000], index=["Electricity", "NaturalGas", "Gasoline", "Mobility"],
                               columns=["Network_ext"])
    parameters = {'Network_ext': Network_ext, "DailyDist": {'short': 10}, "Population": 20, "ff_EV": 1.56}
    set_indexed = {"Distances": ["short"]}

    units = infrastructure.initialize_units(scenario, grids, district_data=True)

    # Define maximum rent affordable (optional)
    reho = ActorsProblem(qbuildings_data=qbuildings_data, units=units, grids=grids, cluster=cluster, scenario=scenario, method=method, DW_params={'max_iter': 5}, solver="gurobiasl")
    reho.parameters['renter_expense_max'] = actors.generate_renter_expense_max_new(qbuildings_data, income=70000)

    # Set value / sampling range for actors epsilon
    #max_profit_utility = reho.get_max_profit_actor("Utility")
    bounds = {"Owners": [0.0, 0.0], "ECM": [0.0, 0]}
    reho.sample_actors_epsilon(bounds=bounds, n_samples=1, ins_target = [0,0.1,0.2])

    #Run actor-based optimization
    reho.actor_decomposition_optimization()

    # Save results
    reho.save_results(format=["pickle"], filename='6a')
