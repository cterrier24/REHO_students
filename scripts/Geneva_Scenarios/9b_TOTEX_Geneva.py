from pickle import FALSE

from reho.model.actors_problem import *
from utils import remove_nan_QBuilding

if __name__ == '__main__':
    # For 9a and 9b the epsilon constraints of actors_problem.mod should me change to:
    # renter_expense_max;  -1e10;  -1e10;  -1e10;

    for i in [9]:#,4,5,6,7,8,9,10]:
        #path = '/home/wang2/REHO_students'
        case_study = i
        df_case_study = pd.read_csv('data/case_study.csv')
        district_boundary = df_case_study.loc[case_study]['boundary']
        # Set building parameters
        reader = QBuildingsReader()
        reader.establish_connection('Suisse')
        neighborhood_type = df_case_study.loc[case_study]['case_study']
        # Set building parameters
        qbuildings_data = reader.read_db(district_boundary=district_boundary,
                                         district_id=int(df_case_study.loc[case_study]['id_neighborhood']))
        qbuildings_data = remove_nan_QBuilding(qbuildings_data)
        era = np.sum([qbuildings_data["buildings_data"][b]['ERA'] for b in qbuildings_data["buildings_data"]])

        print(f"✅ QBuilding data {neighborhood_type} imported successfully.")
        # Select clustering options for weather data
        cluster = {'Location': 'Geneva', 'Attributes': ['T', 'I', 'W'], 'Periods': 10, 'PeriodDuration': 24}

        # Set scenario
        scenario = dict()
        scenario['Objective'] = 'TOTEX'
        scenario['EMOO'] = {}
        scenario['specific'] =['unidirectional_service','unidirectional_service2']
        scenario["name"] = "actors"

        # Choose energy system structure options
        scenario['exclude_units'] = ['ElectricBike_district','ICE_district']
        scenario['enforce_units'] = []

        # Set method options
        method = {'actors_problem': True, "refurbishment": False, "parallel_computation": True,
                  "save_streams": False, "save_timeseries": True, "save_data_input": True,"print_logs": True,
                  'district-scale': True}

        # Initialize available units and grids
        grids = infrastructure.initialize_grids({'Electricity': {"Cost_demand_cst": 0.1, "Cost_supply_cst": 0.3},
                                                 'NaturalGas': {"Cost_demand_cst": 0.25, "Cost_supply_cst": 0.25},
                                                 'Mobility': {"Cost_demand_cst": 0.1, "Cost_supply_cst": 3}})

        # available capacities of networks [Electricity]
        grids["Electricity"]["ReinforcementOfNetwork"] = np.array(
            [100, 250, 400, 630, df_case_study.loc[case_study]['P_peak'] * 3, df_case_study.loc[case_study]['P_peak'] * 3.1,
             df_case_study.loc[case_study]['P_peak'] * 3.2, df_case_study.loc[case_study]['P_peak'] * 3.5,
             df_case_study.loc[case_study]['P_peak'] * 4, df_case_study.loc[case_study]['P_peak'] * 6, 1e7])
        grids["NaturalGas"]["ReinforcementOfNetwork"] = np.array(
            [400, 600, 1000, 2000, 1e6])
        grids["Mobility"]["ReinforcementOfNetwork"] = np.array([2000,5000])#, 4000, 6000, 10000, 1e6

        # existing capacities of networks
        Network_ext = pd.DataFrame([df_case_study.loc[case_study]['P_peak'] * 3, 2000, 2000],
                                   index=["Electricity", "NaturalGas", "Mobility"],
                                   columns=["Network_ext"])


        parameters = {'Network_ext': Network_ext,
                      "DailyDist": {'short': float(df_case_study.loc[case_study]['Distance'])}, "Population": era / 46,
                      "ff_EV": 1.56}

        set_indexed = {"Distances": ["short"]}

        units = infrastructure.initialize_units(scenario, grids, district_data=True, building_data="../examples/data/units_adapted.csv")

        reho = ActorsProblem(qbuildings_data=qbuildings_data, units=units, parameters=parameters, grids=grids,
                             cluster=cluster, scenario=scenario, method=method, DW_params={'max_iter': 4},
                             solver="gurobiasl")

        modal_split = pd.DataFrame({"min_short": [0.0, 0.0, 0.0, 0.0], "max_short": [0.1, 0.4, 1, 1]},
                                   index=['MD', 'PT', 'cars', 'EV_district'])

        reho.modal_split = modal_split

        bounds = {"Owners": [0.0, 0.0], "ECM": [0.0, 0]}
        reho.sample_actors_epsilon(bounds=bounds, n_samples=1, ins_target=[0])

        # Run actor-based optimization
        reho.actor_decomposition_optimization()

        # Save results
        #reho.save_results(format=["pickle"], filename=f'9b_{neighborhood_type}_Actors_SCITAS')
        reho.save_results(format=["pickle"], filename=f'9b_{neighborhood_type}_TOTEX')
