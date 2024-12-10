######################################################################################################################
#--------------------------------------------------------------------------------------------------------------------#
#---OVERARCHING Public Transport MODEL
#--------------------------------------------------------------------------------------------------------------------#
######################################################################################################################

# [1] https://www.hess-ag.ch/fileadmin/user_upload/Hess/Bus/lighTram/lighTram25/Flyer_lighTram25/Flyer_lighTram25DC_VBL_FR_Web.pdf 

# --------------------------------------------- PARAMETERS ---------------------------------------------
param Bus_demand_profile{p in Period, t in Time[p]};
param Metro_demand_profile{p in Period, t in Time[p]};
param Bus_traffic_profile{p in Period, t in Time[p]};
param Metro_traffic_profile{p in Period, t in Time[p]};

param n_rames default 40;                                                                               # nombre actuel de rames de métro, fixé car pas de prise en compte de nouveaux investissement dans ce moyen de transport, à changer uniquement pour simuler des années à venir
param n_trolley default 100;                                                                            # nombre de trolleybus en 2024
param n_ebus default 5;                                                                                 # nombre de bus électriques en 2024
param n_dieselbus default 162;                                                                          # nombre de bus diesel en 2024
param trolley_power default 200;                                                                        # consommation électrique (kW) des trolleybus via les cables [1]
param metro_power default 200;                                                                          # estimation conso élec (kW) du métro lausannois
param taux_trolleybus_district default 0.37;                                                            # % de trolleybus dans la flotte tl en 2024

param dist_moy_trolley default 0.31;                                                                    # distance moyenne entre deux arrêts de bus (qlq), utilisée pour générer les bus_demand_profile
param dist_moy_metro default 0.47;                                                                      # distance moyenne entre deux arrêts de métro, utilisée pour générer les metro_demand_profile

# --------------------------------------------- VARIABLES ---------------------------------------------
var trolley_demand{p in Period, t in Time[p]};
var metro_demand{p in Period, t in Time[p]};

# --------------------------------------------- CONSTRAINTS ---------------------------------------------
subject to TP_c1{p in Period, t in Time[p]}:
sum{u in UnitsOfType['PT_bus']} Units_supply['Mobility',u,p,t] <= Bus_demand_profile[p,t];

subject to TP_c1bis{u in UnitsOfType['PT_metro'], p in Period, t in Time[p]}:
Units_supply['Mobility',u,p,t] <= Metro_demand_profile[p,t];

subject to trolleybus_cst:
Units_Mult['TrolleyBus_district'] >= n_trolley;

subject to ebus_cst:
Units_Mult['ElectricBus_district'] >= n_ebus;

subject to dieselbus_cst:
Units_Mult['DieselBus_district'] >= n_dieselbus;

subject to metro_cst:
Units_Mult['Metro_district'] >= n_rames;

subject to trolleybus_charging{p in Period, t in Time[p]}:
trolley_demand[p,t] = Bus_traffic_profile[p,t] * trolley_power * (dist_moy_trolley / Mode_Speed['TrolleyBus_district']) * taux_trolleybus_district;

subject to metro_charging{p in Period, t in Time[p]}:
metro_demand[p,t] = Metro_traffic_profile[p,t] * metro_power * (dist_moy_metro / Mode_Speed['Metro_district']);
