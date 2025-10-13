from pickle import FALSE

from reho.model.actors_problem import *
from utils import remove_nan_QBuilding, get_renter_param

import time
from scipy.stats import qmc

if __name__ == '__main__':

    # Define sensitivity analysis parameter combinations
    sa_params = [
        [1, 0.0187572, 0.95704925],
        [2, 0.06008296, 0.74852435],
        [3, 0.09667693, 0.82600038],
        [4, 0.0437743, 0.6012367],
        [5, 0.04274315, 0.75444953],
        [6, 0.08162992, 0.54586777],
        [7, 0.07302606, 0.90366302],
        [8, 0.02330948, 0.67883413],
        [9, 0.02836094, 0.86849569],
        [10, 0.06718315, 0.58123568],
        [11, 0.08677107, 0.96924332],
        [12, 0.0369872, 0.69821476],
        [13, 0.05005631, 0.91587906],
        [14, 0.09136145, 0.62856171],
        [15, 0.06610292, 0.79691909],
        [16, 0.01317694, 0.5258258]
    ]

    for n, i_rate, renter_affordability in sa_params:
        for i in [3, 4, 5, 6]:
            case_study = i
            df_case_study = pd.read_csv('scripts/examples/Geneva_Scenarios/case_study.csv')
            neighborhood_type = df_case_study.loc[case_study]['case_study']

            print(f'🔄 SA: {n}/16, 🏘️:{neighborhood_type}')
            district_boundary = df_case_study.loc[case_study]['boundary']
            # Set building parameters
            qbuildings_data = pd.read_pickle('scripts/examples/Geneva_Scenarios/qbuildings_data.pickle')[
                neighborhood_type]
            # reader = QBuildingsReader()
            # reader.establish_connection('Suisse')
            # qbuildings_data = reader.read_db(district_boundary=district_boundary,
            #                                district_id=int(df_case_study.loc[case_study]['id_neighborhood']))
            # qbuildings_data = remove_nan_QBuilding(qbuildings_data)
            print(f"✅ QBuilding data {neighborhood_type} imported successfully.")
            cluster = {'Location': 'Geneva', 'Attributes': ['T', 'I', 'W'], 'Periods': 10, 'PeriodDuration': 24}

            # Set scenario
            scenario = dict()
            scenario['Objective'] = 'TOTEX'
            scenario['EMOO'] = {}
            scenario['specific'] = ['unidirectional_service', 'unidirectional_service', 'Renter_noSub']
            scenario["name"] = "actors"

            # Choose energy system structure options
            scenario['exclude_units'] = ['ICE_district', 'ElectricBike_district']
            scenario['enforce_units'] = []

            # Set method options
            method = {'actors_problem': True, "refurbishment": True, "parallel_computation": True,
                      "save_streams": False, "save_timeseries": True, "save_data_input": True, "print_logs": True,
                      'district-scale': True}

            # Initialize available units and grids
            # Initialize available units and grids
            grids = infrastructure.initialize_grids(
                {'Electricity': {"Cost_demand_cst": 0.1, "Cost_supply_cst": 0.3},
                 'NaturalGas': {"Cost_demand_cst": 0.25, "Cost_supply_cst": 0.25},
                 'Mobility': {"Cost_demand_cst": 0.1, "Cost_supply_cst": 3}})

            # available capacities of networks [Electricity]
            grids["Electricity"]["ReinforcementOfNetwork"] = np.array(
                [100, 250, 400, 630, df_case_study.loc[case_study]['P_peak'] * 3,
                 df_case_study.loc[case_study]['P_peak'] * 3 + 630,
                 df_case_study.loc[case_study]['P_peak'] * 3 + 630 * 2,
                 df_case_study.loc[case_study]['P_peak'] * 3 + 630 * 3,
                 df_case_study.loc[case_study]['P_peak'] * 3 + 630 * 4,
                 df_case_study.loc[case_study]['P_peak'] * 4, 1e7])
            grids["NaturalGas"]["ReinforcementOfNetwork"] = np.array(
                [400, 600, 1000, 2000, 1e6])
            grids["Mobility"]["ReinforcementOfNetwork"] = np.array([2000, 4000, 6000, 10000, 1e6])

            # existing capacities of networks
            Network_ext = pd.DataFrame([df_case_study.loc[case_study]['P_peak'] * 3, 2000, 6000],
                                       index=["Electricity", "NaturalGas", "Mobility"],
                                       columns=["Network_ext"])

            era = np.sum([qbuildings_data["buildings_data"][b]['ERA'] for b in qbuildings_data["buildings_data"]])

            renter_ref = get_renter_param("", neighborhood_type)

            parameters = {'Network_ext': Network_ext,
                          "DailyDist": {'short': float(df_case_study.loc[case_study]['Distance'])},
                          "Population": era / 46,
                          "ff_EV": 1.56,
                          'renter_ref': renter_ref,
                          'renter_affordability': renter_affordability,
                          'i_rate': i_rate
                          }
            set_indexed = {"Distances": ["short"]}

            units = infrastructure.initialize_units(scenario, grids, district_data=True,
                                                    building_data="scripts/examples/data/units_adapted.csv")

            reho = ActorsProblem(qbuildings_data=qbuildings_data, units=units, parameters=parameters, grids=grids,
                                 cluster=cluster, scenario=scenario, method=method, DW_params={'max_iter': 4},
                                 solver="gurobiasl")

            # reho.parameters['renter_expense_max'] = actors.generate_renter_expense_max_new(qbuildings_data, income=70000)

            modal_split = pd.DataFrame({"min_short": [0.0, 0.0, 0.0, 0.0], "max_short": [0.1, 0.4, 1, 1]},
                                       index=['MD', 'PT', 'cars', 'EV_district'])

            reho.modal_split = modal_split

            bounds = {"Owners": [0.0, 0.0], "ECM": [0.0, 0]}
            reho.sample_actors_epsilon(bounds=bounds, n_samples=1, ins_target=[0])

            # Run actor-based optimization
            reho.actor_decomposition_optimization()

            reho.save_results(format=["pickle"], filename=f'9d_{neighborhood_type}_i{i_rate:.3f}_r{renter_affordability:.3f}')
