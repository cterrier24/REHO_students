from reho.model.reho import *


if __name__ == '__main__':

    # Set building parameters
    reader = QBuildingsReader()
    # reader.establish_connection('Geneva')
    # qbuildings_data = reader.read_db(transformer=234, nb_buildings=1)
    qbuildings_data = reader.read_csv(buildings_filename=os.path.join(os.getcwd(),'data','buildings','buildings_11230.gpkg'),nb_buildings=2)  # read data 

    # Select clustering options for weather data
    cluster = {'Location': 'Geneva', 'Attributes': ['T', 'I', 'W'], 'Periods': 10, 'PeriodDuration': 24}

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
    reho = REHO(qbuildings_data=qbuildings_data, units=units, grids=grids, cluster=cluster, scenario=scenario, method=method, solver="gurobi")
    reho.single_optimization()

    # Save results
    reho.save_results(format=['xlsx', 'pickle'], filename='1a')
