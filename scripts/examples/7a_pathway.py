import os
import numpy as np
import pandas as pd
import copy
from reho.model.reho import *

if __name__ == '__main__':

    ####//////////////////////////////////////////////////////////////////////////////////////////////////////////////####
    ######################################################################################################################
    ######################################################################################################################
    #--------------------------------------------------------------------------------------------------------------------#
    # 1. Initialization and general parameters definition
    #--------------------------------------------------------------------------------------------------------------------#
    ######################################################################################################################
    ######################################################################################################################
    ####//////////////////////////////////////////////////////////////////////////////////////////////////////////////####
    
    
    
    ###########################
    #### Script parameters ####
    ###########################

    # Global parameters
    objective_global = 'TOTEX'
    is_jed = True # select whether running on jed or not 
    transformers = [30393247, 6581812, 6584004, 6580296, 6580056, 6581817, 6584147, 6581281, 6583684, 6581376, 6581369] #[30393247, 6584004, 6581817, 6581369, 6583684, 6581812, 6581281, 6581376, 6580056, 6581000, 6580296]
    nb_buildings = 10 # The number of buildings per district to treat from the database. Set to None if want all the district
    opti_solver = 'gurobi'
    ng_cost_supply_cst = 0.09
    transformer=3658


    # Pathway parameters
    N_iter_pathway = 6
    y_start = 2024
    y_stop = 2050
    k=0.1
    k_int=int(np.round(k*1000))  
    c=2037

    scenario_name = "pathway_example"

    # Dict of all REHO models:
    reho_models = dict()
    reho_models[transformer] = dict()




    #############################
    #### Mobility parameters ####
    #############################

    # Number of EV per ERA: f_EV
    era_cap=46.5 #[m^2/cap] Surface per capita. Couldn't find ERA, took simple surface per capita. Source: https://www.bfs.admin.ch/bfs/fr/home/statistiques/construction-logement/logements/conditions-habitation/surface-habitant.html
    cap_home=2.18 #[cap/home] Number of people per home. Source: https://ajour.ch/fr/story/172547/le-mnage-suisse-moyen-compte-218-personnes
    vehicle_home=6/100*3+23/100*2+49/100*1 #[vehicle/home] Number of vehicle per home. Source:https://www.bfs.admin.ch/asset/fr/24310776
    f_EV=vehicle_home/cap_home/era_cap
    # N_vehicles=vehicle_home/cap_home/era_cap*era

    # Share of EV in 2024 and 2050
    EV_share_2024=6.32/100 # source:https://www.bfs.admin.ch/bfs/en/home/statistics/mobility-transport/transport-infrastructure-vehicles/vehicles/road-vehicles-stock-level-motorisation.html
    # EV_share_2024=3.3/100 # source:https://www.swissinfo.ch/eng/business/share-of-electric-cars-inches-upwards-in-switzerland/48905588
    EV_share_2050=1

    # Create the dict to send to the pathway:
    EV_data={}
    EV_data['factor_EV']=f_EV
    EV_data['EV_year']=np.linspace(y_start,y_stop,N_iter_pathway)
    EV_data['EV_share_pathway']=np.array([EV_share_2024+i*(EV_share_2050-EV_share_2024)/(N_iter_pathway-1) for i in range(N_iter_pathway)]) 


    # Insert parameters to add mobility to the model
    # The goal is to specify that only EV are used in the district. We do not want to model the whole fleet of vehicles. Therefore, the growing EV share will be approximated by the Population parameter in the mobility model. 
    parameters = {}
    parameters['max_share_cars']=1 # Allow to be only cars 
    parameters['min_share_EV'] = 0.95
    parameters['max_share_EV'] = 1   
    parameters['DailyDist']=30/0.9 # Assumption: 30km per person per day. Since this number is large for fulfilling it only with EV, The number of vehicles will be equal to the Population.mption: 30km per person per day. Since this number is large for fulfilling it only with EV, The number of vehicles will be equal to the Population.
    


    ###############################
    #### Renovation parameters ####
    ###############################

    # Renovation parameters 
    renovation_rate = 0.01
    SH_limit_renovation = 70 #[kWh/m2_era/y] Below 60, it is not necessary to renovate
    SH_goal_renovation = 60 #[kWh/m2_era/y]



    ########################
    #### DHN parameters ####
    ########################

    share_DHN_2050 = 0.7 # The goal is to have around 50% of the buildings connected in 2050, in the zones where DHN will be developped.
    dhn_2024 = np.array([[0],[0],[0],[0],[1],[1],[0],[0],[0],[0]]) # Buildings connected to DHN initially
    dhn_connectable_2050 = np.array([0,0,0,0,1,1,1,1,1,1]) # Buildings that can be connected to DHN in 2050



    ##################################
    #### Reinforcement parameters ####
    ##################################

    # Reinforcement cost parameters
    reinf_inv = pd.read_csv(os.path.join(os.getcwd(), path_to_infrastructure, 'reinforcement_inv.csv'),
                        index_col='parameter')
    
    # Reinforcement options
    Tr_Reinforcement_options = np.array([63.0, 100.0, 160.0, 250.0, 400.0, 500.0, 630.0, 1000.0,1250.0,1600.0,3200.0,4800.0]) 
    Line_Reinforcement_options = np.array([5,10,20,30,40,50,60,70,80,100,150,200])

    # Existing grid
    Transformer_Ext_district = 63
    Line_Length_buildings = np.array([15,15,10,10,20,20,20,10,10,10]) # np.array([[15],[15],[10],[10],[20],[20],[20],[20],[15],[15]])
    Line_Ext_buildings = np.array([10,10,10,10,10,10,10,10,10,10]) # np.array([[10],[10],[10],[10],[10],[10],[10],[10],[10],[10]])


    ################################################
    #### Load buildings file and current system ####
    ################################################


    # Load the buildings data file
    reader = QBuildingsReader()
    qbuildings_data = reader.read_csv(buildings_filename=os.path.join(os.getcwd(),'data','buildings.csv'),nb_buildings=nb_buildings)

    # Select weather data
    cluster = {'Location': 'Fribourg', 'Attributes': ['I', 'T', 'W'], 'Periods': 10, 'PeriodDuration': 24}


    ####//////////////////////////////////////////////////////////////////////////////////////////////////////////////####
    ######################################################################################################################
    ######################################################################################################################
    #--------------------------------------------------------------------------------------------------------------------#
    # 2. Initial state of the system, in 2024.
    #--------------------------------------------------------------------------------------------------------------------#
    ######################################################################################################################
    ######################################################################################################################
    ####//////////////////////////////////////////////////////////////////////////////////////////////////////////////####
    

    #Initialize scenario
    scenario = dict()
    scenario['Objective'] = objective_global
    scenario['name'] = 'initial_system_2024'
    scenario['specific']=['enforce_OIL_Boiler', # Enforce Oil boiler Units_Use to 1 on buildings heated by Oil boiler
                          'enforce_HeatPump', # Enforce Oil boiler Units_Use to 1 on buildings heated by HeatPump boiler
                          'enforce_NG_Boiler', # Enforce Oil boiler Units_Use to 1 on buildings heated by NG boiler
                          'enforce_DHN_hex_in', # Enforce DHN_hex_in Units_Use to 1 on buildings heated by DHN
                          'enforce_PV', # Enforce PV Units_Use to 1 on buildings that have PV
                          'enforce_PV_Units_Mult', # Enforce PV Units_Mult="specified_value" on buildings that have PV
                          'unidirectional_service', # Add unidirectional charging for EV
                          'unidirectional_service2', # Add unidirectional charging for EV
                          'enforce_nvehicles_to_pop', # Enforce the number of EV to be equal to the Population parameter
                          'no_2_heating_system', # Do not allow two different heating systems (Exple: not NG boiler and heatpump simultaneously)
                          'no_ElectricalHeater_without_HP'] # Do not allow to install an electrical heater when there is no HeatPump
    scenario['exclude_units'] = ['ThermalSolar','Battery','Battery_district','NG_Cogeneration','HeatPump_Geothermal_district','HeatPump_Geothermal','HeatPump_DHN','NG_Cogeneration_district','NG_Boiler_district']


    # Enter method parameters
    method = {"building-scale": True,"update_units_costs":True,'no_public_transport':True} # Remove public transports


    # Initialize Grids
    grids = infrastructure.initialize_grids({'Electricity': {},'NaturalGas': {"Cost_supply_cst": ng_cost_supply_cst},'Heat': {}, 'Oil':{},'Mobility':{}})

    
    # Initialize units
    units = infrastructure.initialize_units(scenario, grids,district_data=True)

    # Compute the district total ERA
    era = sum([qbuildings_data['buildings_data'][i]['ERA'] for i in qbuildings_data['buildings_data'].keys()])

    # Specify additional parameters for DHN:
    parameters["T_DHN_supply_cst"]=np.repeat(100.0, len(qbuildings_data['buildings_data']))
    parameters["T_DHN_return_cst"]=np.repeat(80.0, len(qbuildings_data['buildings_data']))

    # Send the reinforcement options
    grids['Electricity']['ReinforcementTrOfLayer'] = Tr_Reinforcement_options
    grids['Electricity']['ReinforcementLineOfLayer'] = {h: Line_Reinforcement_options for h in qbuildings_data['buildings_data'].keys()}



    ################################
    #### Initialize REHO object ####
    ################################

    # Initialize object
    reho_initial=REHO(qbuildings_data=qbuildings_data, units=units, grids=grids, cluster=cluster, scenario=scenario,
                        method=method, solver=opti_solver, parameters=parameters)


    ########################
    ##### Fix the units ####
    ########################

    # HeatPump to install in specific houses.
    reho_initial.parameters['HeatPump_install'] = np.array([[1],[1],[0],[0],[0],[0],[0],[0],[0],[0]])

    # OIL_Boiler to install in specific house
    reho_initial.parameters['OIL_Boiler_install']= np.array([[0],[0],[1],[1],[0],[0],[0],[0],[0],[0]])

    # DHN_hex_in to install only in specific house
    reho_initial.parameters['DHN_hex_in_install'] = dhn_2024

    # NG_Boiler to install only in specific house
    reho_initial.parameters['NG_Boiler_install']= np.array([[0],[0],[0],[0],[0],[0],[1],[1],[1],[1]])

    # PV to install only in specific houses. The capacity is specified using 'PV_install_Units_Mult'
    reho_initial.parameters['PV_install'] = np.array([[1],[1],[0],[0],[0],[0],[0],[0],[0],[0]])
    reho_initial.parameters['PV_install_Units_Mult'] = np.array([[5],[5],[0],[0],[0],[0],[0],[0],[0],[0]])



    ##########################################
    #### Insert reinforcement parameters #####
    ##########################################

    Transformer_Ext = [Transformer_Ext_district if j=='Electricity' else 0 for j in reho_initial.infrastructure.grids.keys()]

    Line_Length = []
    Line_Ext = []
    i=0
    for h in reho_initial.infrastructure.House:
        Line_Length.append([Line_Length_buildings[i] if j=='Electricity' else 0 for j in reho_initial.infrastructure.grids.keys()])
        Line_Ext.append([Line_Ext_buildings[i] if j=='Electricity' else 0 for j in reho_initial.infrastructure.grids.keys()])
        i+=1
    
    reho_initial.parameters['Transformer_Ext'] = Transformer_Ext
    reho_initial.parameters['Line_Length'] = Line_Length
    reho_initial.parameters['Line_Ext'] = Line_Ext



    ##################
    #### Optimize ####
    ##################

    # Run optimization
    reho_initial.single_optimization()
    results_actual = reho_initial.results['initial_system_2024'][0]



    ####//////////////////////////////////////////////////////////////////////////////////////////////////////////////####
    ######################################################################################################################
    ######################################################################################################################
    #--------------------------------------------------------------------------------------------------------------------#
    # 3. Maximum PV in the buildings
    #--------------------------------------------------------------------------------------------------------------------#
    ######################################################################################################################
    ######################################################################################################################
    ####//////////////////////////////////////////////////////////////////////////////////////////////////////////////####
    

    reho_initial.scenario['specific'].remove('enforce_PV_Units_Mult')
    reho_initial.scenario['specific'].remove('enforce_PV')
    reho_initial.scenario['specific'].append('enforce_PV_max')

    reho_initial.single_optimization(Pareto_ID=1)
    reho_initial





    ####//////////////////////////////////////////////////////////////////////////////////////////////////////////////####
    ######################################################################################################################
    ######################################################################################################################
    #--------------------------------------------------------------------------------------------------------------------#
    # 4. Pathway
    #--------------------------------------------------------------------------------------------------------------------#
    ######################################################################################################################
    ######################################################################################################################
    ####//////////////////////////////////////////////////////////////////////////////////////////////////////////////####
    

    ######################################
    #### Initialize the general model ####
    ######################################

    #Initialize scenario
    scenario = dict()
    scenario['Objective'] = objective_global
    scenario['name'] = transformer
    scenario['exclude_units'] = ['ThermalSolar','Battery','Battery_district','NG_Cogeneration','HeatPump_Geothermal_district','HeatPump_Geothermal','HeatPump_DHN','NG_Cogeneration_district','NG_Boiler_district']

    # Add unidirectional charging for EV, enforce the number of EV to be equal to the Population parameter
    scenario['specific'] = ['unidirectional_service','unidirectional_service2','enforce_nvehicles_to_pop','no_2_heating_system','no_ElectricalHeater_without_HP']

    # Enter method parameters
    method = {"building-scale": True,"update_units_costs":True,'no_public_transport':True} # Remove public transports

    # Initialize Grids
    grids = infrastructure.initialize_grids({'Electricity': {},'NaturalGas': {"Cost_supply_cst": ng_cost_supply_cst},'Heat': {}, 'Oil':{},'Mobility':{}})

    # Initialize units
    units = infrastructure.initialize_units(scenario, grids,district_data=True)

    # Compute the district total ERA
    era = sum([qbuildings_data['buildings_data'][i]['ERA'] for i in qbuildings_data['buildings_data'].keys()])

    # Specify additional parameters for DHN:
    parameters["T_DHN_supply_cst"]=np.repeat(100.0, len(qbuildings_data['buildings_data']))
    parameters["T_DHN_return_cst"]=np.repeat(80.0, len(qbuildings_data['buildings_data']))

    # Send the reinforcement options
    grids['Electricity']['ReinforcementTrOfLayer'] = Tr_Reinforcement_options
    grids['Electricity']['ReinforcementLineOfLayer'] = {h: Line_Reinforcement_options for h in qbuildings_data['buildings_data'].keys()}


    ################################
    #### Initialize REHO object ####
    ################################

    # Initialize object
    reho_model=REHO(qbuildings_data=qbuildings_data, units=units, grids=grids, cluster=cluster, scenario=scenario,
                        method=method, solver=opti_solver, parameters=parameters)
    

    ###############################################
    #### Insert reinforcement cost parameters #####
    ###############################################

    reinf_inv = pd.read_csv(os.path.join(os.getcwd(), path_to_infrastructure, 'reinforcement_inv_real.csv'),
                        index_col='parameter')
    for i in reinf_inv.index:
        data = []
        if 'Line' in i:
            for h in reho_model.infrastructure.House:
                data.append([reinf_inv.loc[i].value if j=='Electricity' else 0 for j in reho_model.infrastructure.grids.keys()])
            data = np.array(data)
        else:
            data = np.array([reinf_inv.loc[i].value if j=='Electricity' else 0 for j in reho_model.infrastructure.grids.keys()])
        reho_model.parameters[i] = data



    ####################
    #### Renovation ####
    ####################

    # Get space heating demand
    heat_demand = pd.DataFrame([
                            [h,
                            qbuildings_data['buildings_data'][h]['egid'],
                            (results_actual['df_Annuals'].xs('SH').loc[h]['Demand_MWh']+results_actual['df_Annuals'].xs('DHW').loc[h]['Demand_MWh'])*1000,
                            (results_actual['df_Annuals'].xs('SH').loc[h]['Demand_MWh']+results_actual['df_Annuals'].xs('DHW').loc[h]['Demand_MWh'])*1000/qbuildings_data['buildings_data'][h]['ERA'],
                            qbuildings_data['buildings_data'][h]['U_h'],
                            ] for h in qbuildings_data['buildings_data'].keys()],
                            columns=['Hub','egid','heat_demand','heat_demand_m2','U_h'])

    # Add DHN informations
    heat_demand['DHN_connectable_2050'] = dhn_connectable_2050
    heat_demand['DHN_connected'] = dhn_2024

    # Add the information whether HP is installed (Useful for DHN)
    df_HP = results_actual['df_Unit'][results_actual['df_Unit'].index.str.contains('HeatPump')].reset_index()
    df_HP['Hub']=df_HP['Unit'].apply(lambda x: x.split('_')[-1])
    heat_demand = pd.merge(heat_demand,df_HP.drop(columns='Unit').groupby('Hub').agg('sum')[['Units_Use']].reset_index(),on='Hub').rename(columns={'Units_Use':'HP_installed'})
    heat_demand['HP_installed'] = np.round(heat_demand['HP_installed']) # Sometimes, Units_Use is not exactly 1
    heat_demand['DHN_connectable_2050'] = heat_demand.apply(lambda x:0 if x['HP_installed']==1 else x['DHN_connectable_2050'],axis=1) # Remove connectability where there is already heat pumps

    # Decide which buildings should be renovated
    heat_demand['to_renovate_bool']=heat_demand['heat_demand_m2']>=SH_goal_renovation

    # Define the U_h after renovation
    heat_demand['SH_goal'] = SH_goal_renovation
    heat_demand['U_h_renovated'] = heat_demand.apply(lambda x: x['U_h']*x['SH_goal']/x['heat_demand_m2'],axis=1)

    # Define the U_h after renovation of buildings that are already good as what they are now.
    heat_demand['U_h_renovated'] = heat_demand.apply(lambda x: x['U_h_renovated'] if x['to_renovate_bool'] else x['U_h'],axis=1)

    # Create the list of buildings to renovate and when
    renovated_init=np.sum(heat_demand['to_renovate_bool']==False)/len(heat_demand)
    EMOO_list_renov=[int(np.round((renovated_init+(y_stop-y_start)/(N_iter_pathway-1)*i*renovation_rate)*len(heat_demand))) for i in range(N_iter_pathway)]
    EMOO_list_renov=[key if key<=len(heat_demand) else len(heat_demand) for key in EMOO_list_renov] # If the share of renovation reaches 100%, cap it, or else it doesn't make sense
    renov_data,renov_bool,temp=reho_model.select_values_random(values=heat_demand['U_h_renovated'].to_list(),
                                    initial_selection=list(1-heat_demand['to_renovate_bool']),
                                    steps=EMOO_list_renov)
    
    # Compute all buildings that will be renovated in 2050
    heat_demand['renovated_final'] = np.array([renov_bool[i] for i in renov_bool.keys()]).sum(axis=0)[:,0]
    heat_demand['renovated_final'] = heat_demand.apply(lambda x: x['renovated_final'] if x['to_renovate_bool'] else 0,axis=1)

    ####################
    #### Future CAD ####
    ####################

    # The goal here is to select randomly a set of buildings that will use DHN

    # Get number of buildings already connected to DHN
    DHN_connected_init=heat_demand['DHN_connected'].sum()

    # Get number of buildings that can be connected to DHN
    DHN_connected_final=share_DHN_2050*heat_demand['DHN_connectable_2050'].sum()

    # Define a rate to go from the initial point to 80% of the maximum of buidings connectable
    DHN_rate=(DHN_connected_final-DHN_connected_init)/(y_stop-y_start)

    if DHN_rate<0: # If the required share of dhn is already satisfied, the rate will be negative and this means dhn should be uninstalled, which is wrong. Practically: this means that the share is a minimum share, in the case of initial installation greater than required share.
        DHN_rate=0

    # Create the list of total number of buildings that must be connected for each timestep
    EMOO_list_DHN=[int(np.round((DHN_connected_init+(y_stop-y_start)/(N_iter_pathway-1)*i*DHN_rate))) for i in range(N_iter_pathway)]

    # Select buildings randomly. Assumption: Do not connect to DHN where there is already HP
    initial_selection=list(heat_demand['DHN_connected']+1-heat_demand['DHN_connectable_2050']) # Consider the initial selection to be all buildings that are connected or that cannot be connected. This way,the function will only choose on the buildings where it can install DHN
    dhn_data,dhn_bool,dhn_bool_tot = reho_model.select_values_random(values=heat_demand['DHN_connectable_2050'].to_list(), # Consider where HP installed to have a value of 0. This allows dhn_bool_tot to be zero where there is already HP
                                    initial_selection=initial_selection,
                                    steps=EMOO_list_DHN)

    heat_demand['DHN_connected_final'] = heat_demand['DHN_connected'].values+np.array([dhn_bool[i] for i in list(dhn_bool.keys())[1:]]).sum(axis=0)[:,0]

    

    ########################################################
    #### Specific constraints to progressively increase ####
    ########################################################

    reho_model.scenario['specific'].append('enforce_PV')
    reho_model.scenario['specific'].append('enforce_PV_Units_Mult')
    reho_model.scenario['specific'].append('enforce_DHN_hex_in')

    # Initially, set DHN to install nowhere. This parameter will get updated in the pathway function
    reho_model.parameters['DHN_hex_in_install']=np.array([[0] for h in reho_model.infrastructure.House])



    ####################################
    #### Get the pathway parameters ####
    ####################################
    
    # Get the number of house that installed a PV 
    PV_tot_int = reho_initial.results['initial_system_2024'][1]['df_Unit'].loc[reho_initial.results['initial_system_2024'][1]['df_Unit'].index.str.contains('PV')]['Units_Use'].sum()

    # Get the number of house that installed a PV 
    PV_init_int = int(np.round(results_actual['df_Unit'][results_actual['df_Unit'].index.str.contains('PV')]['Units_Use'].sum()))


    # Compute partial logistic if transition already started, else full logistic with symmetric c value
    if PV_init_int==0:
        EMOO_list_PV, y_span = reho_model.get_logistic(E_start=PV_init_int,E_stop=PV_tot_int,y_start=y_start,y_stop=y_stop,k=k,c=c,n=N_iter_pathway,final_value=False,starting_value=True)
    else:
        EMOO_list_PV, y_span = reho_model.get_logistic_partial(E_start=0,E_stop=PV_tot_int,y_start=y_start,y_stop=y_stop,k=k,y=y_start,E=PV_init_int,n=N_iter_pathway,final_value=False)

    EMOO_list_PV = [int(np.round(i)) for i in EMOO_list_PV] # Transform the steps to integers




    #######################################################################
    #### Aggregate all pathway data: EMOO, years, mobility, renovation ####
    #######################################################################

    # Create the dict to send to the pathway function
    pathway_data={}
    pathway_data['y_span'] = y_span
    pathway_data['renovation'] = renov_data
    pathway_data['EV'] = EV_data
    pathway_data['DHN'] = dhn_bool_tot
    pathway_data['kPV'] = k
    pathway_data['c'] = c
    pathway_data['EMOO']={}
    pathway_data['EMOO']['PV'] = {}
    pathway_data['EMOO']['PV']['Units_Mult'] ={}
    pathway_data['EMOO']['PV']['Units_Use'] ={}



    #######################################################
    #### Assign randomly the installation of PV and HP ####
    #######################################################

    # Notes:
    #   1. No HP where there is or will be DHN
    #   2. Must correct the already installed PV capacities. Indeed, it is assumed that buildings that already installed will not install again.
    #   3. Must correct the already installed HP capacities. Indeed, it is assumed that buildings that already installed will not install again.
    #   4. HP must sum Air-source and Ground-source


    # Create the list of Units_Use and Units_Mult constraint for each step.
    # Note: The possible PV cpacities are given by the enforce_PV_max scenario above. However, the already installed capacities do not correspond necessary to these maximum values. It is therefore necessary to modify the list. 
    df_PV_installable = reho_initial.results['initial_system_2024'][1]['df_Unit'].loc[(reho_initial.results['initial_system_2024'][1]['df_Unit'].index.str.contains('PV')) & ~(reho_initial.results['initial_system_2024'][1]['df_Unit'].index.str.contains('district'))] # What the max scenario gave
    installable_PV = [np.sum([row['Units_Mult'] for index,row in df_PV_installable.iterrows() if index.split('_')[-1]==h]) for h in reho_model.infrastructure.House] # In the form of a list ordered correctly

    df_PV_installed = results_actual['df_Unit'].loc[(results_actual['df_Unit'].index.str.contains('PV')) & ~(results_actual['df_Unit'].index.str.contains('district'))] # What is already installed
    installed_PV = [np.sum([row['Units_Mult'] for index,row in df_PV_installed.iterrows() if index.split('_')[-1]==h]) for h in reho_model.infrastructure.House] # In the form of a list ordered correctly

    installable_PV_future = [installable_PV[num] if installed_PV[num]==0 else installed_PV[num] for num in range(len(installable_PV))] # Correction of the list of available capacities
    initial_selection_PV = [1 if key!=0 else 0 for key in installed_PV] # Creation of the initial installed capacities boolean
    
    pathway_data['EMOO']['PV']['Units_Mult'],temp,pathway_data['EMOO']['PV']['Units_Use']=reho_model.select_values_random(values=installable_PV_future,
                                    initial_selection=initial_selection_PV,
                                    steps=EMOO_list_PV) # Random attribution


    ########################################
    #### Specify existing installations ####
    ########################################

    # Insert actual system:
    existing_units = results_actual['df_Unit'][['Units_Mult']]
    reho_model.parameters["Units_Ext"] = np.array([[existing_units.loc[key]['Units_Mult'] if key in existing_units.index else 0 for key in [s for s in reho_model.infrastructure.Units if h==s.split('_')[-1]]] for h in reho_model.infrastructure.House]) # To ensure the right value is given.



    ##############################
    #### Run the optimization ####
    ##############################

    reho_model.pathway_building_scale(pathway_data=pathway_data,existing_init=results_actual)



    ######################
    #### Save results ####
    ######################

    reho_model.results[transformer][0]=results_actual


    df_list=['df_Grid_t','df_Unit_t','df_Buildings_t']
    for key in reho_model.results[transformer].keys():
        for df_to_remove in df_list:
            if df_to_remove in reho_model.results[transformer][key].keys():
                del reho_model.results[transformer][key][df_to_remove]


    keys = copy.deepcopy(list(reho_model.results[transformer].keys()))
    for key in keys:
        reho_model.results[transformer][key]['pathway']=pathway_data
        reho_model.results[transformer][key]={0:reho_model.results[transformer][key]} # Add a new depth to the dict: the configuration
        reho_model.results[transformer].update({int(np.round(y_span[key])):reho_model.results[transformer].pop(key)})


    reho_models[transformer][k_int] = reho_model.results[transformer]

    # Save everything in one transformer
    filename='results/' + scenario_name + '.pickle'

    f = open(filename, 'wb')
    pickle.dump(reho_models, f)
    f.close()


