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
param Ebus_charging_profile{p in Period, t in Time[p]};

param n_rames default 0;                                                                               # nombre de rames de métro prises dans le district, initialisé dans mobility_generator
param n_rames_tot default 40;                                                                          # nombre total de rames de métro, à changer uniquement pour simuler des années à venir
param n_trolley default 0;#100;                                                                            # nombre de trolleybus en 2024
param n_ebus default 0;# 5;                                                                                 # nombre de bus électriques en 2024
param n_dieselbus default 0; #162;                                                                          # nombre de bus diesel en 2024
param trolley_kwh default 2.42;                                                                         # consommation électrique (kWh/km) des trolleybus via les cables [1]
param metro_kwh default 3;                                                                              # consommation électrique (kWh/km) du métro lausannois (moyenne m1+m2)
param taux_trolleybus_district default 0.37;                                                            # % de trolleybus dans la flotte tl en 2024
param n_class;                                                                                          # nombre de districts dans la classe représentée par le typical district étudié

param dist_moy_trolley default 0.31;                                                                    # distance moyenne (en km) entre deux arrêts de bus (qlq), utilisée pour générer les bus_demand_profile
param dist_moy_metro default 0.47;                                                                      # distance moyenne (en km) entre deux arrêts de métro, utilisée pour générer les metro_demand_profile
param cst_relax default 0.05;                                                                           # constante de relaxation pour le chargement des bus électriques à batterie

# --------------------------------------------- VARIABLES ---------------------------------------------
var trolley_demand{u in UnitsOfType['PT_bus'], p in Period, t in Time[p]};
var metro_demand{u in UnitsOfType['PT_metro'], p in Period, t in Time[p]};
var ebus_demand{u in UnitsOfType['PT_bus'], p in Period, t in Time[p]};

# --------------------------------------------- CONSTRAINTS ---------------------------------------------
subject to TP_c1_2024{p in Period, t in Time[p]}:
sum{u in UnitsOfType['PT_bus']} Units_supply['Mobility',u,p,t] <= Bus_demand_profile[p,t];

subject to TP_c1bis_2024{u in UnitsOfType['PT_metro'], p in Period, t in Time[p]}:
Units_supply['Mobility',u,p,t] <= Metro_demand_profile[p,t];

subject to TP_c1_2030{p in Period, t in Time[p]}:
sum{u in UnitsOfType['PT_bus']} Units_supply['Mobility',u,p,t] <= Bus_demand_profile[p,t] * 1.18;       # car la flotte de bus augmente de 18% par rapport à 2024   

subject to TP_c1bis_2030{u in UnitsOfType['PT_metro'], p in Period, t in Time[p]}:
Units_supply['Mobility',u,p,t] <= Metro_demand_profile[p,t] * 1.5;                                      # car la flotte augmente de 50% par rapport à 2024 (nouvelle ligne m3)

subject to TP_c1_2050{p in Period, t in Time[p]}:
sum{u in UnitsOfType['PT_bus']} Units_supply['Mobility',u,p,t] <= Bus_demand_profile[p,t] * 1.31;       # car la flotte augmente de 31% par rapport à 2024 (hypothèse de 350 au total)

subject to TP_c1bis_2050{u in UnitsOfType['PT_metro'], p in Period, t in Time[p]}:
Units_supply['Mobility',u,p,t] <= Metro_demand_profile[p,t] * 1.5;                                      # car la flotte augmente de 50% par rapport à 2024 (même situation que 2030)

subject to trolleybus_cst:
Units_Mult['TrolleyBus_district'] >= n_trolley;

subject to ebus_cst:
Units_Mult['ElectricBus_district'] >= n_ebus;

subject to dieselbus_cst:
Units_Mult['DieselBus_district'] >= n_dieselbus;

subject to metro_cst:
Units_Mult['Metro_district'] >= n_rames;

subject to trolleybus_charging{p in Period, t in Time[p]}:
trolley_demand['TrolleyBus_district',p,t] = Bus_traffic_profile[p,t] * trolley_kwh * dist_moy_trolley * (n_trolley / n_class);

subject to metro_charging{p in Period, t in Time[p]}:
metro_demand['Metro_district',p,t] = Metro_traffic_profile[p,t] * metro_kwh * dist_moy_metro * (n_rames / n_class);

# contraint le chargement des bus à batterie avec un peu de flexibilité
subject to ebus_charging1{p in Period, t in Time[p]}:
ebus_demand['ElectricBus_district',p,t] <=  Ebus_charging_profile[p,t] * (n_ebus / n_class) * (1 + cst_relax); 

subject to ebus_charging2{p in Period, t in Time[p]}:
ebus_demand['ElectricBus_district',p,t] >=  Ebus_charging_profile[p,t] * (n_ebus / n_class) * (1 - cst_relax);