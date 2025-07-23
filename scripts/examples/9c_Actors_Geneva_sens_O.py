from pickle import FALSE

from reho.model.actors_problem import *

import math
import time
from scipy.stats import qmc

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

def get_renter_param(base_path: str, neighborhood_type: str) -> pd.Series:
    """
    Compute the renter_ref series for a given neighborhood scenario.

    Parameters:
    - base_path: str, the root directory containing the 'scripts/examples/results' subfolder.
    - neighborhood_type: str, one of the scenario identifiers (e.g., 'Center', 'Villa', 'Rural').

    Returns:
    - pd.Series named 'renter_ref', indexed by building/hub labels, with computed cost allocations.

    Raises:
    - FileNotFoundError if the pickle file does not exist.
    """
    # Build the full pickle file path
    file_path = (
        f"{base_path}/scripts/examples/results/9a_{neighborhood_type}_"
        "TOTEX_wo_El_wo_Res.pickle"
    )
    try:
        data = pd.read_pickle(file_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find file: {file_path}")

    ERA = data['actors'][0]['df_Buildings']['ERA']
    df_econ = data['actors'][0]['df_Economics']
    reinf = (
        data['actors'][0]['df_Grid']
            .xs('Network')
            .xs('Electricity')['ReinforcementCost']
    )

    renter_series = pd.Series(index=ERA.index, name="renter_ref")
    total_era = ERA.sum()

    for hub in ERA.index:
        net_costs = (
            df_econ
            .xs('Network', level='Hub', axis=0)
            .xs('costs')
        )
        local_costs = (
            df_econ
            .xs(hub, level='Hub', axis=0)
            .xs('costs')
        )
        weight = ERA[hub] / total_era
        renter_series[hub] = (
            net_costs['investment']['ICE_district'] * weight
            + local_costs['investment'].get('NG_Boiler', 0)
            + local_costs['operation'].get('costs_Electricity', 0)
            + net_costs['operation']['costs_Gasoline'] * weight
            + local_costs['operation'].get('costs_NaturalGas', 0)
            + reinf * weight
        )

    return renter_series

if __name__ == '__main__':

    for renter_affordability, i_rate in [[0.0187572 , 0.95704925],
       [0.06008296, 0.74852435],
       [0.09667693, 0.82600038],
       [0.0437743 , 0.6012367 ],
       [0.04274315, 0.75444953],
       [0.08162992, 0.54586777],
       [0.07302606, 0.90366302],
       [0.02330948, 0.67883413],
       [0.02836094, 0.86849569],
       [0.06718315, 0.58123568],
       [0.08677107, 0.96924332],
       [0.0369872 , 0.69821476],
       [0.05005631, 0.91587906],
       [0.09136145, 0.62856171],
       [0.06610292, 0.79691909],
       [0.01317694, 0.5258258]]:
            for i in range(0,3):
                print( '✅✅✅✅RENTER AFFORDABILITY:',renter_affordability,'i=', i,'✅✅✅✅')
                #path = '/Users/ziqian/Desktop/MA/EnergyScope/REHO'
                path = '/home/wang2/REHO_students'
                case_study = i  #Center: 0; Villa:1 ; Rural:2
                df_case_study = pd.read_csv(path + '/scripts/examples/data/case_study.csv')
                neighborhood_type = df_case_study.loc[case_study]['case_study']

                # Set building parameters
                qbuildings_data = pd.read_pickle(path + f'/scripts/examples/results/data/QBuildings_{neighborhood_type}.pickle')
                print(f"✅ QBuilding data {neighborhood_type} imported successfully.")
                # Select clustering options for weather data
                cluster = {'Location': 'Geneva', 'Attributes': ['T', 'I', 'W'], 'Periods': 10, 'PeriodDuration': 24}

                # Set scenario
                scenario = dict()
                scenario['Objective'] = 'TOTEX'
                scenario['EMOO'] = {}
                scenario['specific'] =['unidirectional_service','Renter_noSub']
                scenario["name"] = "actors"

                # Choose energy system structure options
                scenario['exclude_units'] = ['Bike_district','ICE_district', 'ElectricBike_district']
                scenario['enforce_units'] = []

                # Set method options
                method = {'actors_problem': True, "refurbishment": True, "parallel_computation": True,
                          "save_streams": False, "save_timeseries": True, "save_data_input": True,"print_logs": False,
                          'district-scale': True}

                # Initialize available units and grids
                grids = infrastructure.initialize_grids({'Electricity': {"Cost_demand_cst": 0.1, "Cost_supply_cst": 0.3},
                                                         'NaturalGas': {"Cost_demand_cst": 0.25, "Cost_supply_cst": 0.25},
                                                         'Gasoline': {"Cost_demand_cst": 0.25, "Cost_supply_cst": 0.25},
                                                         'Mobility': {"Cost_demand_cst": 0.1, "Cost_supply_cst": 3}})

                # available capacities of networks [Electricity]
                grids["Electricity"]["ReinforcementOfNetwork"] = np.array([100, 250, 400, df_case_study.loc[case_study]['P_peak'] * 3,630, 1000, 2000, 4000])
                grids["Mobility"]["ReinforcementOfNetwork"] = np.array([2000])
                grids["Gasoline"]["ReinforcementOfNetwork"] = np.array([2000])

                # existing capacities of networks
                Network_ext = pd.DataFrame([ df_case_study.loc[case_study]['P_peak'] * 3, 2000, 2000, 2000], index=["Electricity", "NaturalGas", "Gasoline", "Mobility"],
                                           columns=["Network_ext"])

                era = np.sum([qbuildings_data["buildings_data"][b]['ERA'] for b in qbuildings_data["buildings_data"]])

                parameters = {'Network_ext': Network_ext, "DailyDist": {'short': float(df_case_study.loc[case_study]['Distance'])}, "Population": era / 46, "ff_EV": 1.56,
                              'renter_affordability': renter_affordability, 'i_rate': i_rate, 'renter_ref': get_renter_param(path, neighborhood_type)}
                set_indexed = {"Distances": ["short"]}

                units = infrastructure.initialize_units(scenario, grids, district_data=True, building_data=path+"/scripts/examples/data/units_adapted.csv")

                reho = ActorsProblem(qbuildings_data=qbuildings_data, units=units, parameters=parameters, grids=grids,
                                     cluster=cluster, scenario=scenario, method=method, DW_params={'max_iter': 5},
                                     solver="gurobiasl")
                reho.parameters['renter_expense_max'] = actors.generate_renter_expense_max_new(qbuildings_data, income=70000)

                modal_split = pd.DataFrame({"min_short": [0.0, 0.0, 0.0, 0.0], "max_short": [0.1, 0.2, 1, 1]},
                                           index=['MD', 'PT', 'cars', 'EV_district'])

                reho.modal_split = modal_split

                bounds = {"Owners": [0.0, 0.0], "ECM": [0.0, 0]}
                reho.sample_actors_epsilon(bounds=bounds, n_samples=1, ins_target=[0])

                # Run actor-based optimization
                reho.actor_decomposition_optimization()

                # Save results
                #reho.save_results(format=["pickle"], filename=f'9b_{neighborhood_type}_Actors_SCITAS')
                reho.save_results(format=["pickle"], filename=f'9d_{neighborhood_type}_i{i_rate}_r{renter_affordability}_Actors_SCITAS_{time.strftime("%m%d%H%M")}')
