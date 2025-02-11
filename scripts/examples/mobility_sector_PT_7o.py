######################################################################################################################################
#### Run the scenarios with no PV, HP or EH to obtain the maximum capacity of each typical district.                              ####
#### !!! Comment the lines in master_problem.py regarding the reading of the file PT.mod in the if loop (Ctrl+F to find this if)  ####
######################################################################################################################################


from reho.model.reho import *
from reho.plotting import plotting
import math


year = 2024
transformer = 3216

dict_param_3195 = { "Population": 2500,               # 71 buildings
                    "DailyDist" : {"long" : 20,
                                   'short' : 10},
                    "n_rames": 0,
                    "n_trolley": 0,
                    "n_ebus": 0,
                    "n_dieselbus": 48,
                    "n_class": 24
                }


dict_param_3217 = { "Population": 7500,               # 107 buildings     
                    "DailyDist" : {"long" : 20,
                                   'short' : 10},
                    "n_rames": 0,
                    "n_trolley": 0,
                    "n_ebus": 0,
                    "n_dieselbus": 28,
                    "n_class": 14
                }


dict_param_3230 = { "Population": 6000,               # 190 buildings             
                    "DailyDist" : {"long" : 20,
                                   'short' : 10},
                    "n_rames": 0,
                    "n_trolley": 46,
                    "n_ebus": 3,
                    "n_dieselbus": 74,
                    "n_class": 37
                }


dict_param_10481 = { "Population": 130,               # 1 seul building 
                    "DailyDist" : {"long" : 20,
                                   'short' : 10},
                    "n_rames": 0,
                    "n_trolley": 6,
                    "n_ebus": 0,
                    "n_dieselbus": 10,
                    "n_class": 5
                }


dict_param_10491 = { "Population": 85,               # 1 seul building 
                    "DailyDist" : {"long" : 20,
                                   'short' : 10},
                    "n_rames": 0,
                    "n_trolley": 0,
                    "n_ebus": 0,
                    "n_dieselbus": 0,
                    "n_class": 5
                }


dict_param_3216 = { "Population": 470,               # 7 buildings 
                    "DailyDist" : {"long" : 20,
                                   'short' : 10},
                    "n_rames": 5,
                    "n_trolley": 6,
                    "n_ebus": 0,
                    "n_dieselbus": 9,
                    "n_class": 5,
                    "year" : 2024,
                    "transformer" : 3216
                }


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

if __name__ == '__main__':

    # Set building parameters
    reader = QBuildingsReader()
    reader.establish_connection('Suisse')
    qbuildings_data = reader.read_db(transformer=transformer, nb_buildings=7)   
    qbuildings_data = remove_nan_QBuilding(qbuildings_data)    

    # Select weather data
    cluster = {'Location': 'Geneva', 'Attributes': ['I', 'T', 'W'], 'Periods': 10, 'PeriodDuration': 24}

    # Set scenario
    scenario = dict()
    scenario['Objective'] = 'TOTEX'
    scenario['EMOO'] = {}
    scenario['exclude_units'] = ['NG_Cogeneration','HeatPump','ElectricalHeater','PV','ThermalSolar']
    #scenario['enforce_units'] = ['EV_district']

    # Initialize available units and grids
    grids = infrastructure.initialize_grids({'Electricity': {},
                                             'NaturalGas': {},
                                             'FossilFuel': {},
                                             })
    units = infrastructure.initialize_units(scenario,grids,district_data=True)    

    # Set method options
    method = {'building-scale': True}


    # SCENARIO 1
    scenario['name'] = 'totex_0'

    # Set parameters
    parameters = {}

    # Run optimization
    reho = REHO(qbuildings_data=qbuildings_data, units=units, grids=grids, parameters=parameters, cluster=cluster, scenario=scenario, method=method, solver="gurobiasl")
    reho.single_optimization()

    # Plot results
    plotting.plot_sankey(reho.results['totex_0'][0], label='EN_long', color='ColorPastel', title=f"Sankey diagram {transformer}_{year}").show()


    # SCENARIO 2
    scenario['name'] = 'totex'

    # Activate the constraint forcing the charging profile of electric vehicles. 
    # scenario['specific'] = ['EV_chargingprofile1','EV_chargingprofile2']

    # # Run optimization
    # reho.scenario = scenario
    # reho.single_optimization()

    # Save results
    reho.save_results(format=['xlsx', 'pickle'], filename=f'7o_{transformer}', erase_file=True)

