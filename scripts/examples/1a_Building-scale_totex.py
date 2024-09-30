from reho.model.reho import *


if __name__ == '__main__':

    buildings_filename = os.path.join(os.getcwd(),'data_old','buildings','buildings_11230.gpkg')#str(Path(__file__).parent / 'data_old' / 'buildings.csv')

    # Set building parameters
    # Load your buildings from a csv file instead of reading the database
    reader = QBuildingsReader()
    qbuildings_data = reader.read_csv(buildings_filename=buildings_filename, nb_buildings=2)

    # Select clustering options for weather data
    cluster = {'Location': 'Fribourg', 'Attributes': ['T', 'I', 'W'], 'Periods': 10, 'PeriodDuration': 24}

    # Set scenario
    scenario = dict()
    scenario['Objective'] = 'TOTEX'
    scenario['name'] = 'totex'
    scenario['exclude_units'] = ['Battery', 'NG_Cogeneration']
    scenario['enforce_units'] = []
    #scenario['EMOO'] = {'EMOO_PV':0.3}

    # Initialize available units and grids
    grids = infrastructure.initialize_grids()
    units = infrastructure.initialize_units(scenario, grids)

    # Set method options
    method = {'building-scale': True}

    # Run optimization
    reho = REHO(qbuildings_data=qbuildings_data, units=units, grids=grids, cluster=cluster, scenario=scenario, method=method, solver="HiGHS")
    reho.single_optimization()

    # Save results
    reho.save_results(format=['xlsx', 'pickle'], filename='1a')
