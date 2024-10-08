from reho.model.reho import *
from reho.plotting import plotting


if __name__ == '__main__':

    buildings_filename = os.path.join(os.getcwd(),'data_old','buildings.csv')#str(Path(__file__).parent / 'data_old' / 'buildings.csv')

    nb_buildings=2
    # Set building parameters
    # Load your buildings from a csv file instead of reading the database
    reader = QBuildingsReader()
    qbuildings_data = reader.read_csv(buildings_filename=buildings_filename,nb_buildings=nb_buildings)
    era = sum([qbuildings_data['buildings_data'][i]['ERA'] for i in qbuildings_data['buildings_data'].keys()])

    # Select clustering options for weather data
    cluster = {'Location': 'Fribourg', 'Attributes': ['T', 'I', 'W'], 'Periods': 10, 'PeriodDuration': 24}

    # Set scenario
    scenario = dict()
    scenario['Objective'] = 'TOTEX'
    scenario['name'] = 'totex'
    scenario['exclude_units'] = ['Battery', 'NG_Cogeneration']
    #scenario['enforce_units'] = ['HeatPump_DHN']
    #scenario["specific"] = ["enforce_DHN"]
    # Initialize available units and grids
    grids = infrastructure.initialize_grids({'Electricity': {},
                                             'NaturalGas': {"Cost_supply_cst": 0.6, "Cost_demand_cst": 0.16},
                                             'Heat': {"Cost_supply_cst": 0.03, "Cost_demand_cst": 0.01}})
    units = infrastructure.initialize_units(scenario, grids, district_data=True)

    # Set method options
    # You can specify if the DHN is based on CO2. If not, a water DHN is assumed.
    method = {'building-scale': True}#, 'DHN_CO2': True}

    # Set specific parameters
    # Specify the temperature of the DHN
    parameters={}
    parameters = {'T_DHN_supply_cst': np.repeat(100.0, nb_buildings), "T_DHN_return_cst": np.repeat(80.0, nb_buildings)}

    # Run optimization
    reho = REHO(qbuildings_data=qbuildings_data, units=units, grids=grids, parameters=parameters, cluster=cluster, scenario=scenario, method=method, solver="HiGHS")
    reho.get_DHN_costs()  # run one optimization forcing DHN to find costs DHN connection per house
    reho.single_optimization()  # run optimization with DHN costs

    # Save results
    reho.save_results(format=['xlsx', 'pickle'], filename='3e')

    # Plot results
    plotting.plot_performance(reho.results, plot='costs', indexed_on='Scn_ID', label='EN_long', title="Economical performance").show()
    plotting.plot_sankey(reho.results['totex'][0], label='EN_long', color='ColorPastel', title="Sankey diagram").show()
