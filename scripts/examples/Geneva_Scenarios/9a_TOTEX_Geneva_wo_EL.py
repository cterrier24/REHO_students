from pickle import FALSE

from reho.model.actors_problem import *
from utils import remove_nan_QBuilding

if __name__ == '__main__':
    for i in range(3,11):
        case_study = i
        df_case_study = pd.read_csv('scripts/examples/Geneva_Scenarios/case_study.csv')
        neighborhood_type = df_case_study.loc[case_study]['case_study']
        print(f"🏘️  Starting scenario for {neighborhood_type} neighborhood...")
        district_boundary = df_case_study.loc[case_study]['boundary']
        # Set building parameters
        qbuildings_data = pd.read_pickle('scripts/examples/Geneva_Scenarios/qbuildings_data.pickle')[neighborhood_type]
        #reader = QBuildingsReader()
        #reader.establish_connection('Suisse')
        #qbuildings_data = reader.read_db(district_boundary=district_boundary,
        #                                district_id=int(df_case_study.loc[case_study]['id_neighborhood']))
        #qbuildings_data = remove_nan_QBuilding(qbuildings_data)
        print(f"✅ QBuilding data {neighborhood_type} imported successfully.")
        cluster = {'Location': 'Geneva', 'Attributes': ['T', 'I', 'W'], 'Periods': 10, 'PeriodDuration': 24}

        # Set scenario
        scenario = dict()
        scenario['Objective'] = 'TOTEX'
        scenario['EMOO'] = {}
        scenario['specific'] = ['unidirectional_service','unidirectional_service2', 'Renter_noSub']
        scenario["name"] = "actors"

        # Choose energy system structure options
        scenario['exclude_units'] = ['HeatPump', 'Battery','PV',
                                     'ElectricalHeater_DHW', 'ElectricalHeater_SH','ThermalSolar']
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
        grids["Electricity"]["ReinforcementOfNetwork"] = np.array([100, 250, 400, 630, 1000, 2000, 4000, 10000, 15000,
                                                                   df_case_study.loc[case_study]['P_peak'] * 3,25000,30000, 35000,40000])
        grids["NaturalGas"]["ReinforcementOfNetwork"] = np.array([100, 250, 400, 630, 1000, 2000, 4000, 6000, 8000, 10000,
                                                                  15000,20000])
        grids["Mobility"]["ReinforcementOfNetwork"] = np.array([6000, 10000])
        grids["Gasoline"]["ReinforcementOfNetwork"] = np.array([4000])

        # existing capacities of networks
        Network_ext = pd.DataFrame([df_case_study.loc[case_study]['P_peak'] * 3, 6000, 4000, 6000], index=["Electricity", "NaturalGas", "Gasoline", "Mobility"],
                                   columns=["Network_ext"])

        era = np.sum([qbuildings_data["buildings_data"][b]['ERA'] for b in qbuildings_data["buildings_data"]])

        parameters = {'Network_ext': Network_ext, "DailyDist": {'short': float(df_case_study.loc[case_study]['Distance'])}, "Population": era / 46}
        set_indexed = {"Distances": ["short"]}

        units = infrastructure.initialize_units(scenario, grids, district_data=True, building_data="scripts/examples/data/units_adapted.csv")

        reho = ActorsProblem(qbuildings_data=qbuildings_data, units=units, parameters=parameters, grids=grids,
                             cluster=cluster, scenario=scenario, method=method, DW_params={'max_iter': 3},
                             solver="gurobiasl")
        #reho.parameters['renter_expense_max'] = actors.generate_renter_expense_max_new(qbuildings_data, income=70000)

        modal_split = pd.DataFrame({"min_short": [0.0, 0.0, 0.0, 0.0, 0.0], "max_short": [0.1, 0.4, 1, 1, 0.0]},
                                   index=['MD', 'PT', 'cars', 'ICE_district','EV_district'])

        reho.modal_split = modal_split

        bounds = {"Owners": [0.0, 0.0], "ECM": [0.0, 0]}
        reho.sample_actors_epsilon(bounds=bounds, n_samples=1, ins_target=[0])

        # Run actor-based optimization
        reho.actor_decomposition_optimization()

        # Save results
        reho.save_results(format=["pickle"], filename=f'9a_{neighborhood_type}_TOTEX_wo_El')