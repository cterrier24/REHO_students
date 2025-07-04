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
    for i in [0,1,2]:
        path = '/home/wang2/'
        case_study = i  #Center: 0; Villa:1 ; Rural:2
        df_case_study = pd.read_csv(path + 'REHO_students/scripts/examples/data/case_study.csv')
        neighborhood_type = df_case_study.loc[case_study]['case_study']
        # Set building parameters
        reader = QBuildingsReader()
        reader.establish_connection('Suisse')
        qbuildings_data = reader.read_db(district_boundary='neighborhoods', district_id= int(df_case_study.loc[case_study]['id_neighborhood']))
        qbuildings_data = remove_nan_QBuilding(qbuildings_data)

        # Select clustering options for weather data
        cluster = {'Location': 'Geneva', 'Attributes': ['T', 'I', 'W'], 'Periods': 10, 'PeriodDuration': 24}

        # Set scenario
        scenario = dict()
        scenario['Objective'] = 'TOTEX'
        scenario['EMOO'] = {}
        scenario['specific'] =['unidirectional_service']
        scenario["name"] = "actors"

        # Choose energy system structure options
        scenario['exclude_units'] = ['Bike_district','EV_district', 'ElectricBike_district','HeatPump', 'Battery','PV', 'EV_Charger_district', 'ThermalSolar']
        scenario['enforce_units'] = []

        # Set method options
        method = {'actors_problem': True, "refurbishment": False, "parallel_computation": True,
                  "save_streams": False, "save_timeseries": True, "save_data_input": True,"print_logs": True,
                  'district-scale': True}

        # Initialize available units and grids
        grids = infrastructure.initialize_grids({'Electricity': {"Cost_demand_cst": 0.1, "Cost_supply_cst": 0.3},
                                                 'NaturalGas': {"Cost_demand_cst": 0.25, "Cost_supply_cst": 0.25},
                                                 'Gasoline': {"Cost_demand_cst": 0.25, "Cost_supply_cst": 0.25},
                                                 'Mobility': {"Cost_demand_cst": 0.1, "Cost_supply_cst": 3}})

        # available capacities of networks [Electricity]
        grids["Electricity"]["ReinforcementOfNetwork"] = np.array([100, 250, df_case_study.loc[case_study]['P_peak'] * 3, 630, 1000, 2000, 4000])
        grids["Mobility"]["ReinforcementOfNetwork"] = np.array([2000])
        grids["Gasoline"]["ReinforcementOfNetwork"] = np.array([2000])

        # existing capacities of networks
        Network_ext = pd.DataFrame([df_case_study.loc[case_study]['P_peak'] * 3, 2000, 2000, 2000], index=["Electricity", "NaturalGas", "Gasoline", "Mobility"],
                                   columns=["Network_ext"])

        era = np.sum([qbuildings_data["buildings_data"][b]['ERA'] for b in qbuildings_data["buildings_data"]])

        parameters = {'Network_ext': Network_ext, "DailyDist": {'short': float(df_case_study.loc[case_study]['Distance'])}, "Population": era / 46}
        set_indexed = {"Distances": ["short"]}

        units = infrastructure.initialize_units(scenario, grids, district_data=True, building_data=path+"REHO_students/scripts/examples/data/units_adapted.csv")

        reho = ActorsProblem(qbuildings_data=qbuildings_data, units=units, parameters=parameters, grids=grids,
                             cluster=cluster, scenario=scenario, method=method, DW_params={'max_iter': 3},
                             solver="gurobiasl")
        reho.parameters['renter_expense_max'] = actors.generate_renter_expense_max_new(qbuildings_data, income=70000)

        modal_split = pd.DataFrame({"min_short": [0.0, 0.0, 0.0, 0.0, 0.0], "max_short": [0.1, 0.2, 1.0, 1.0, 0.0]},
                                   index=['MD', 'PT', 'cars', 'ICE_district', 'EV_district'])

        reho.modal_split = modal_split
        # Set value / sampling range for actors epsilon
        # max_profit_utility = reho.get_max_profit_actor("Utility")
        bounds = {"Owners": [0.0, 0.0], "ECM": [0.0, 0]}
        reho.sample_actors_epsilon(bounds=bounds, n_samples=1, ins_target=[0])

        #remember to disable network_demand and Unit_demand['','EV_charger_district'] in AP
        # Run actor-based optimization
        reho.actor_decomposition_optimization()

        # Save results
<<<<<<< Updated upstream
        reho.save_results(format=["pickle"], filename=f'9a_{neighborhood_type}_TOTEX_wo_El_1')
=======
        reho.save_results(format=["pickle"], filename=f'9a_{neighborhood_type}_TOTEX_wo_El')
>>>>>>> Stashed changes
