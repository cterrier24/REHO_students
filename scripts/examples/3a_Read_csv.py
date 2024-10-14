from reho.model.reho import *
from reho.plotting import plotting

if __name__ == '__main__':

    nb_buildings = 2

    buildings_filename = os.path.join(os.getcwd(),'data_old','buildings_fribourg.csv')#str(Path(__file__).parent / 'data_old' / 'buildings.csv')

    # Set building parameters
    # Load your buildings from a csv file instead of reading the database
    reader = QBuildingsReader()
    qbuildings_data = reader.read_csv(buildings_filename=buildings_filename,nb_buildings=nb_buildings)
    #qbuildings_data['buildings_data'] = {'Building64':qbuildings_data['buildings_data']['Building64']}
    #qbuildings_data['buildings_data']['Building64']['ERA']=154
    era = sum([qbuildings_data['buildings_data'][i]['ERA'] for i in qbuildings_data['buildings_data'].keys()])
    # Select clustering options for weather data
    cluster = {'Location': 'Fribourg', 'Attributes': ['T', 'I', 'W'], 'Periods': 10, 'PeriodDuration': 24}

    # Set scenario
    scenario = dict()
    scenario['Objective'] = 'TOTEX'
    scenario['name'] = 0
    scenario['exclude_units'] = []
    scenario['enforce_units'] = []
    #scenario['EMOO'] = {'EMOO_PV':0.1} #[kW/m2_ERA]
    #scenario['EMOO'] = {'EMOO_HP':0} #[kW/m2_ERA]
    #scenario['EMOO'] = {'EMOO_HP_upper':0.06,'EMOO_HP_lower':0.08} #[kW/m2_ERA]

    # Initialize available units and grids
    grids = infrastructure.initialize_grids({'Electricity': {},'NaturalGas': {}})#,'Heat': {},'Hydrogen': {},'Oil':{}})
    units = infrastructure.initialize_units(scenario, grids,district_data=True)


    # Set method options
    method = {'building-scale': True}
    DW_params = {'max_iter': 5}

    # Run optimization
    reho = REHO(qbuildings_data=qbuildings_data, units=units, grids=grids, cluster=cluster, scenario=scenario, method=method,DW_params=DW_params, solver="HiGHS")
    reho.single_optimization()

    # Save results
    reho.save_results(format=['xlsx', 'pickle'], filename='3a')

    # Performance plot : costs and gwp
    plotting.plot_performance(reho.results, plot='costs', indexed_on='Pareto_ID', label='EN_long', title="Economical performance").show()