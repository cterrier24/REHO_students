from reho.model.reho import *
from reho.plotting import plotting


if __name__ == '__main__':

    buildings_filename = os.path.join(os.getcwd(),'data_old','selection.gpkg')#str(Path(__file__).parent / 'data_old' / 'buildings.csv')

    # Set building parameters
    # Load your buildings from a csv file instead of reading the database
    reader = QBuildingsReader()
    qbuildings_data = reader.read_csv(buildings_filename=buildings_filename, nb_buildings=7)

    # Select clustering options for weather data
    cluster = {'Location': 'Fribourg', 'Attributes': ['T', 'I', 'W'], 'Periods': 10, 'PeriodDuration': 24}

    # Set scenario
    scenario = dict()
    scenario['Objective'] = 'GWP'
    scenario['name'] = 'totex'
    scenario['exclude_units'] = ['NG_Cogeneration','NG_Boiler']
    scenario['enforce_units'] = ['Battery_district']
    #scenario['EMOO'] = {'EMOO_PV':0.3}

    # Initialize available units and grids
    grids = infrastructure.initialize_grids()
    units = infrastructure.initialize_units(scenario, grids)

    # Set method options
    method = {'district-scale': True}

    # Run optimization
    reho = REHO(qbuildings_data=qbuildings_data, units=units, grids=grids, cluster=cluster, scenario=scenario, method=method, solver="HiGHS")
    reho.single_optimization()

    # Save results
    reho.save_results(format=['xlsx', 'pickle'], filename='1a')

    plotting.plot_sankey(reho.results['totex'][0], label='EN_long', color='ColorPastel').show()
