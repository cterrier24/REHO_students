######################################################################################################################################
#### Run the scenarios with all the technologies (PV+HP) for each typical district.                                               ####
#### Results are available under the xlsx and pkl format. To plot the Sankeys and cost/gwp plots, use 7a_plotting.py              ####
#### _relax_0.3 : when the relaxation constant has been increased to 30% 
#### _fix : latest simulations, with the PT elec consumption corrected for the oral exam
#### _noPVHP : baseline scenario (run with mobility_sector_PT_7a_noPVHP.py)
######################################################################################################################################


from reho.model.reho import *
from reho.plotting import plotting
import math 


############ dictionnaires pour 2024 ##############
dict_param_3195_2024 = { "Population": 2500,               # 71 buildings
                    "DailyDist" : {"long" : 20,
                                   'short' : 10},
                    "n_rames": 25,
                    "n_trolley": 30,
                    "n_ebus": 5,
                    "n_dieselbus": 48,
                    "n_class": 24,
                    "year" : 2024,
                    "transformer" : 3195
                }


dict_param_3217_2024 = { "Population": 7500,               # 107 buildings     
                    "DailyDist" : {"long" : 20,
                                   'short' : 10},
                    "n_rames": 14,
                    "n_trolley": 17,
                    "n_ebus": 0,
                    "n_dieselbus": 28,
                    "n_class": 14,
                    "year" : 2024,
                    "transformer" : 3217
                    #"TransformerCapacity": np.array([730, 1e8, 1e8, 1e8])
                }


dict_param_3230_2024 = { "Population": 6000,               # 190 buildings             
                    "DailyDist" : {"long" : 20,
                                   'short' : 10},
                    "n_rames": 0,
                    "n_trolley": 46,
                    "n_ebus": 0,
                    "n_dieselbus": 74,
                    "n_class": 37,
                    "year" : 2024,
                    "transformer" : 3230,
                    #"TransformerCapacity": np.array([3980, 1e8, 1e8, 1e8])
                }


dict_param_10481_2024 = { "Population": 130,               # 1 seul building 
                    "DailyDist" : {"long" : 20,
                                   'short' : 10},
                    "n_rames": 0,
                    "n_trolley": 6,
                    "n_ebus": 0,
                    "n_dieselbus": 10,
                    "n_class": 5,
                    "year" : 2024,
                    "transformer" : 10481
                }


dict_param_10491_2024 = { "Population": 85,               # 1 seul building 
                    "DailyDist" : {"long" : 20,
                                   'short' : 10},
                    "n_rames": 0,
                    "n_trolley": 0,
                    "n_ebus": 0,
                    "n_dieselbus": 0,
                    "n_class": 5,
                    "year" : 2024,
                    "transformer" : 10491
                }

dict_param_3216_2024 = { "Population": 470,               # 7 buildings 
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


########### dictionnaires pour 2030 #############
dict_param_3195_2030 = { "Population": 2750,               # 71 buildings
                    "DailyDist" : {"long" : 20,
                                   'short' : 10},
                    "n_rames": 25,
                    "n_trolley": 47,
                    "n_ebus": 38,
                    "n_dieselbus": 8,
                    "n_class": 24,
                    "year" : 2030,
                    "transformer" : 3195
                }


dict_param_3217_2030 = { "Population": 8300,               # 107 buildings    
                    "DailyDist" : {"long" : 20,
                                   'short' : 10},
                    "n_rames": 24,
                    "n_trolley": 28,
                    "n_ebus": 22,
                    "n_dieselbus": 5,
                    "n_class": 14,
                    "year" : 2030,
                    "transformer" : 3217
                }


dict_param_3230_2030 = { "Population": 6600,               # 190 buildings             
                    "DailyDist" : {"long" : 20,
                                   'short' : 10},
                    "n_rames": 10,
                    "n_trolley": 73,
                    "n_ebus": 58,
                    "n_dieselbus": 12,
                    "n_class": 37,
                    "year" : 2030,
                    "transformer" : 3230
                }


dict_param_10481_2030 = { "Population": 145,               # 1 seul building 
                    "DailyDist" : {"long" : 20,
                                   'short' : 10},
                    "n_rames": 0,
                    "n_trolley": 10,
                    "n_ebus": 8,
                    "n_dieselbus": 2,
                    "n_class": 5,
                    "year" : 2030,
                    "transformer" : 10481
                }

dict_param_10491_2030 = { "Population": 95,               # 1 seul building
                    "DailyDist" : {"long" : 20,
                                   'short' : 10},
                    "n_rames": 7,
                    "n_trolley": 9,
                    "n_ebus": 7,
                    "n_dieselbus": 2,
                    "n_class": 5,
                    "year" : 2030,
                    "transformer" : 10491
                }

dict_param_3216_2030 = { "Population": 520,               # 7 buildings 
                    "DailyDist" : {"long" : 20,
                                   'short' : 10},
                    "n_rames": 7,
                    "n_trolley": 9,
                    "n_ebus": 7,
                    "n_dieselbus": 2,
                    "n_class": 5,
                    "year" : 2030,
                    "transformer" : 3216
                }


########### dictionnaires pour 2050 #############
dict_param_3195_2050 = { "Population": 3200,               # 71 buildings
                    "DailyDist" : {"long" : 20,
                                   'short' : 10},
                    "n_rames": 25,
                    "n_trolley": 57,
                    "n_ebus": 47,
                    "n_dieselbus": 0,
                    "n_class": 24,
                    "year" : 2050,
                    "transformer" : 3195
                }


dict_param_3217_2050 = { "Population": 9700,               # 107 buildings     
                    "DailyDist" : {"long" : 20,
                                   'short' : 10},
                    "n_rames": 24,
                    "n_trolley": 33,
                    "n_ebus": 27,
                    "n_dieselbus": 0,
                    "n_class": 14,
                    "year" : 2050,
                    "transformer" : 3217
                }


dict_param_3230_2050 = { "Population": 7700,               # 190 buildings       7700    
                    "DailyDist" : {"long" : 20,
                                   'short' : 10},
                    "n_rames": 10,
                    "n_trolley": 87,
                    "n_ebus": 73,
                    "n_dieselbus": 0,
                    "n_class": 37,
                    "year" : 2050,
                    "transformer" : 3230
                }


dict_param_10481_2050 = { "Population": 170,               # 1 seul building 
                    "DailyDist" : {"long" : 20,
                                   'short' : 10},
                    "n_rames": 0,
                    "n_trolley": 12,
                    "n_ebus": 10,
                    "n_dieselbus": 0,
                    "n_class": 5,
                    "year" : 2050,
                    "transformer" : 10481
                }

dict_param_10491_2050 = { "Population": 110,               # 1 seul building
                    "DailyDist" : {"long" : 20,
                                   'short' : 10},
                    "n_rames": 0,
                    "n_trolley": 0,
                    "n_ebus": 0,
                    "n_dieselbus": 0,
                    "n_class": 5,
                    "year" : 2050,
                    "transformer" : 10491
                }

dict_param_3216_2050 = { "Population": 610,               # 7 buildings 
                    "DailyDist" : {"long" : 20,
                                   'short' : 10},
                    "n_rames": 7,
                    "n_trolley": 11,
                    "n_ebus": 9,
                    "n_dieselbus": 0,
                    "n_class": 5,
                    "year" : 2050,
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

cluster_list = [3195, 3217, 3230, 10481, 10491, 3216]
year_list = [2024, 2030, 2050]

building_dict = {3195 : 71, 
                 3217 : 107,
                 3230 : 190,
                 10481 : 1,
                 10491 : 1,             # this district has been substituted with 3216
                 3216 : 7}

dict_param = {2024 : dict(),
              2030 : dict(),
              2050 : dict()}

for year in year_list:
    for cluster in cluster_list:
        name = f'dict_param_{cluster}_{year}'
        dict_param[year][cluster] = locals()[name]

if __name__ == '__main__':

    for year in [2024,2030,2050]:
        start = time.perf_counter()
        for transformer in [3216]:
            # Set building parameters
            reader = QBuildingsReader()
            reader.establish_connection('Suisse')
            qbuildings_data = reader.read_db(transformer=transformer, nb_buildings=building_dict[transformer])   
            qbuildings_data = remove_nan_QBuilding(qbuildings_data)    

            # Select weather data
            cluster = {'Location': 'Geneva', 'Attributes': ['I', 'T', 'W'], 'Periods': 10, 'PeriodDuration': 24}

            # Set scenario
            scenario = dict()
            scenario['Objective'] = 'TOTEX'
            scenario['EMOO'] = {}
            scenario['exclude_units'] = ['NG_Cogeneration','ThermalSolar']
            scenario['enforce_units'] = ['EV_district']

            # Initialize available units and grids
            grids = infrastructure.initialize_grids({'Electricity': {},
                                                    'NaturalGas': {},
                                                    'FossilFuel': {},
                                                    'Mobility': {},
                                                    })
            units = infrastructure.initialize_units(scenario,grids,district_data=True)    

            # Set method options
            method = {'building-scale': True}

            # SCENARIO 1
            scenario['name'] = 'totex'

            # Activate the constraint forcing the charging profile of electric vehicles.
            if year == 2024: 
                scenario['specific'] = ['TP_c1_2024','TP_c1bis_2024']

            if year == 2030: 
                scenario['specific'] = ['TP_c1_2030','TP_c1bis_2030']

            if year == 2050: 
                scenario['specific'] = ['TP_c1_2050','TP_c1bis_2050']

            scenario['specific'] = scenario['specific'] + ['EV_chargingprofile1','EV_chargingprofile2']
            #scenario['specific'] = ['EV_chargingprofile1','EV_chargingprofile2']
    
            # Set parameters
            parameters = dict_param[year][transformer]
            #parameters = dict_param_3195_2030

            # Run optimization
            reho = REHO(qbuildings_data=qbuildings_data, units=units, grids=grids, parameters=parameters, cluster=cluster, scenario=scenario, method=method, solver="gurobiasl")
            reho.single_optimization()


            # Save results
            reho.save_results(format=['pickle'], filename=f'7a_{transformer}_{year}_fix_relax', erase_file=True)

            # Plot results
            #plotting.plot_sankey(reho.results['totex'][0], label='EN_long', color='ColorPastel', title=f"Sankey diagram {transformer}_{year} capacity").show()


        end = time.perf_counter()
        print(f"{year} ran in {(end-start)/60:.2f} minutes")





# anciens districts ou non-étudiés

# dict_param_10680 = {  "Population": 2000,             # 132 buildings, 135000 hab. à Lausanne pour environ 9000 buildings (d'après la ville de Lausanne) => 15 hab/building (et on arrondi le chiffre après)
#                     "DailyDist" : {"long" : 20,
#                                    'short' : 10},
#                     "n_rames": 24,
#                     "n_trolley": 27,
#                     "n_ebus": 2,
#                     "n_dieselbus": 44,
#                     "n_class": 23
#                 }

# dict_param_3175 = {  "Population": 21,                # 1 seul building 
#                     "DailyDist" : {"long" : 20,
#                                    'short' : 10},
#                     "n_rames": 2,
#                     "n_trolley": 1,
#                     "n_ebus": 0,
#                     "n_dieselbus": 2,
#                     "n_class": 1
#                 }

# dict_param_3241 = {  "Population": 15,                # 1 seul building
#                     "DailyDist" : {"long" : 20,
#                                    'short' : 10},
#                     "n_rames": 0,
#                     "n_trolley": 0,
#                     "n_ebus": 0,
#                     "n_dieselbus": 0,
#                     "n_class": 1
#                 }


# dict_param_3242 = {  "Population": 45,                # 3 buildings
#                     "DailyDist" : {"long" : 20,
#                                    'short' : 10},
#                     "n_rames": 0,
#                     "n_trolley": 0,
#                     "n_ebus": 0,
#                     "n_dieselbus": 0,
#                     "n_class": 3
#                 }


# dict_param_10679 = {  "Population": 110,              # 8 buildings
#                     "DailyDist" : {"long" : 20,
#                                    'short' : 10},
#                     "n_rames": 0,
#                     "n_trolley": 0,
#                     "n_ebus": 0,
#                     "n_dieselbus": 0,
#                     "n_class": 8
#                 }