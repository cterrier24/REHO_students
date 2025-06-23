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
    qbuildings_data = reader.read_db(district_id= 2877, nb_buildings=12)
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
    scenario['exclude_units'] = []
    scenario['enforce_units'] = []

    # Set method options
    method = {'actors_problem': True, "refurbishment": True, "parallel_computation": True,
              "save_streams": False, "save_timeseries": False, "save_data_input": True}

    # Initialize available units and grids
    grids = infrastructure.initialize_grids(available_grids={'Electricity': {}, 'NaturalGas': {}, 'Heat':{}, 'Biomethane':{}, 'Mobility': {}
                                                             })

    parameters = {"TransformerCapacity": np.array([5600, 1e8])}
    units = infrastructure.initialize_units(scenario=scenario, grids= grids, district_data=True)

    # Set parameters
    #era = np.sum([qbuildings_data["buildings_data"][b]['ERA'] for b in qbuildings_data["buildings_data"]])

    # here Population is scaled to the number of buildings being optimized (CH : 46m²/cap on average )
    # 35 km/cap/day, 2 categories of distance (D0 : short and D1 : long)
    #parameters = {"Population": era / 46, "DailyDist": {'D0': 25, 'D1': 10}}

    # min max share for each mobility mode and each distance
    #modal_split = pd.DataFrame({"min_D0": [0, 0, 0.4, 0.3], "max_D0": [0.1, 0.3, 0.7, 0.7],
    #                           "min_D1": [0, 0.2, 0.4, 0.3], "max_D1": [0, 0.4, 0.7, 0.7]},
    #                          index=['MD', 'PT', 'cars', 'EV_district'])

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