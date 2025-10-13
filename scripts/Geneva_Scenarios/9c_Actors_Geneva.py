import pickle
from reho.model.actors_problem import *
from utils import remove_nan_QBuilding, get_renter_param
import time

if __name__ == '__main__':
    # For 9c and 9d the epsilon constraints of actors_problem.mod should me change to:
    # renter_affordability * renter_ref[h];
    # (i_rate + 1) * Costs_House_inv[h];
    # i_rate * tau * (sum{u in Units} (Costs_Unit_inv[u]) + Costs_rep);
    # i_rate * DSO_reinforce;

    for i in range(14,23):
        case_study = i
        df_case_study = pd.read_csv('data/case_study.csv')
        neighborhood_type = df_case_study.loc[case_study]['case_study']
        print(f"✅ QBuilding data {neighborhood_type} imported successfully (Progress: 🔄 {i-10} / 12)")
        district_boundary = df_case_study.loc[case_study]['boundary']
        # Set building parameters
        qbuildings_data = pd.read_pickle('data/qbuildings_data_CH.pickle')[neighborhood_type]
        #reader = QBuildingsReader()
        #reader.establish_connection('Suisse')
        #qbuildings_data = reader.read_db(district_boundary=district_boundary,
        #                               district_id=int(df_case_study.loc[case_study]['id_neighborhood']), nb_buildings=2)
        #qbuildings_data = remove_nan_QBuilding(qbuildings_data)
        print(f"✅ QBuilding data {neighborhood_type} imported successfully.")
        cluster = {'Location': 'Geneva', 'Attributes': ['T', 'I', 'W'], 'Periods': 10, 'PeriodDuration': 24}

        # Set scenario
        scenario = dict()
        scenario['Objective'] = 'TOTEX'
        scenario['EMOO'] = {}
        scenario['specific'] =['unidirectional_service','unidirectional_service', 'Renter_noSub']
        scenario["name"] = "actors"

        # Choose energy system structure options
        scenario['exclude_units'] = ['ICE_district', 'ElectricBike_district']
        scenario['enforce_units'] = []

        # Set method options
        method = {'actors_problem': True, "refurbishment": True, "parallel_computation": True,
                  "save_streams": False, "save_timeseries": True, "save_data_input": True,"print_logs": True,
                  'district-scale': True}

        # Initialize available units and grids
        # Initialize available units and grids
        grids = infrastructure.initialize_grids({'Electricity': {"Cost_demand_cst": 0.1, "Cost_supply_cst": 0.3},
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

        renter_ref = get_renter_param("", neighborhood_type, ch=True)

        parameters = {'Network_ext': Network_ext,
                      "DailyDist": {'short': float(df_case_study.loc[case_study]['Distance'])}, "Population": era / 46,
                      "ff_EV": 1.56,
                      'renter_ref':renter_ref}
        set_indexed = {"Distances": ["short"]}

        units = infrastructure.initialize_units(scenario, grids, district_data=True,
                                                building_data="../examples/data/units_adapted.csv")

        reho = ActorsProblem(qbuildings_data=qbuildings_data, units=units, parameters=parameters, grids=grids,
                             cluster=cluster, scenario=scenario, method=method, DW_params={'max_iter': 5},
                             solver="gurobiasl")

        #reho.parameters['renter_expense_max'] = actors.generate_renter_expense_max_new(qbuildings_data, income=70000)

        modal_split = pd.DataFrame({"min_short": [0.0, 0.0, 0.0, 0.0], "max_short": [0.1, 0.4, 1, 1]},
                                   index=['MD', 'PT', 'cars', 'EV_district'])

        reho.modal_split = modal_split

        bounds = {"Owners": [0.0, 0.0], "ECM": [0.0, 0]}
        reho.sample_actors_epsilon(bounds=bounds, n_samples=1, ins_target=[0])

        # Run actor-based optimization
        reho.actor_decomposition_optimization()

        # Save results
        #reho.save_results(format=["pickle"], filename=f'9b_{neighborhood_type}_Actors_SCITAS')
        reho.save_results(format=["pickle"], filename=f'CH/9c_{neighborhood_type}_Actors')
