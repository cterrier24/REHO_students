######################################################################################################################
#--------------------------------------------------------------------------------------------------------------------#
#---OVERARCHING MOBILITY MODEL
#--------------------------------------------------------------------------------------------------------------------#
######################################################################################################################
#-Simple mobility model
# Declare generic parameters and constraints valid for the transport sector

# [1] Federal office of statistic. (2017). Comportement de la population en matière de transports (841–1500; p. 88).


# ----------------------------------------- PARAMETERS ---------------------------------------
param Population default 10; # will multiply the domestic demand. Caution : unlinked default value duplicata in generate_mobility_parameters
set Distances default {"long","short"};
param DailyDist{dist in Distances} default 30.3; # [1] Caution : unlinked default value duplicata in generate_mobility_parameters
param max_travel_time default 3; # 1.3 hours national mean, by default the constraint is relaxed

set transport_Units; # TODO : check if dynamic to the rest of the code
set transport_Units_MD;
set transport_Units_cars;
set transport_Units_PT :={'TrolleyBus_district','ElectricBus_district','DieselBus_district','Metro_district'}; #PT_train enlevé
set transport_PT :={'PT_bus','PT_metro'}; #PT_train enlevé
set Activities := {"work","leisure","travel"}; 
set Districts default {};
param Mode_Speed{u in transport_Units} default 37.1; # [1] Fig G 3.3.1.3 : Vitesse moyenne des utilisateurs des moyens de transport terrestres, en 2015
param Daily_Profile{u in transport_Units,p in Period,t in Time[p]} default 1; # initialized through the function generate_mobility_parameters
param Domestic_energy_pkm{dist in Distances ,p in Period ,t in Time[p]} >= 0;

param max_share{u in transport_Units_MD union transport_Units_cars union transport_PT, dist in Distances} default 1;
param min_share{u in transport_Units_MD union transport_Units_cars union transport_PT, dist in Distances} default 0;

set Modes := {"cars","MD","PT"};
param max_share_modes{m in Modes, dist in Distances} default 1; # [1] G 3.3.1.6 
param min_share_modes{m in Modes, dist in Distances} default 0;

# param Bus_demand_profile{u in UnitsOfType['PT_bus'], p in Period, t in Time[p]};
# param Metro_demand_profile{u in UnitsOfType['PT_metro'], p in Period, t in Time[p]};

# ----------------------------------------- VARIABLES ---------------------------------------
var travel_time{p in Period,t in Time[p]} >= 0 ; #pkm

# Categories of distance
var pkm_supply{u in transport_Units_MD union transport_Units_cars union transport_Units_PT, dist in Distances ,p in Period ,t in Time[p]} >= 0;


#-VARIABLES (for public transport)
#var pkm_PT_train{u in UnitsOfType['EV'], p in Period, t in Time[p]} >= 0;
var pkm_PT_bus{u in UnitsOfType['EV'], p in Period, t in Time[p]} >= 0;    
var pkm_PT_metro{u in UnitsOfType['EV'], p in Period, t in Time[p]} >=0;

# ---------------------------------------- CONSTRAINTS ---------------------------------------

# Categories of distance
# subject to pkm_distancetypes_c1{p in Period,t in Time[p]}: # still needed or not ? => since it's  only params. 
# Domestic_energy["Mobility",p,t] <= sum{dist in Distances} (Domestic_energy_pkm[dist,p,t]);

subject to pkm_distancetypes_c2_1{u in transport_Units_MD union transport_Units_cars union transport_Units_PT, p in PeriodStandard, t in Time[p]}:
sum{dist in Distances} (pkm_supply[u,dist,p,t]) = Units_supply['Mobility',u,p,t];

# subject to pkm_distancetypes_c2_bus{u in UnitsOfType['EV'],p in PeriodStandard,t in Time[p]}:     # plus besoin car inclut désormais dans la contrainte ci-dessus
# sum{dist in Distances} (pkm_supply["PT_bus",dist,p,t]) = pkm_PT_bus[u,p,t];

# subject to pkm_distancetypes_c2_train{u in UnitsOfType['EV'], p in PeriodStandard,t in Time[p]}:
#  sum{dist in Distances} (pkm_supply["PT_train",dist,p,t]) = pkm_PT_train[u,p,t]/dp[p];

# subject to pkm_distancetypes_c2_metro{u in UnitsOfType['EV'], p in PeriodStandard,t in Time[p]}:    # plus besoin car inclut désormais dans la contrainte ci-dessus
# sum{dist in Distances} (pkm_supply["PT_metro",dist,p,t]) = pkm_PT_metro[u,p,t];
# subject to pkm_distancetypes_c2_train{p in PeriodStandard,t in Time[p]}:
# sum{dist in Distances}(pkm_supply["PT_train",dist,p,t] + pkm_supply["PT_bus",dist,p,t]) = Network_supply["Mobility",p,t];


subject to pkm_distancetypes_c3{dist in Distances, p in PeriodStandard, t in Time[p]}:
Domestic_energy_pkm[dist,p,t] = sum{u in transport_Units_MD union transport_Units_cars union transport_Units_PT} (pkm_supply[u,dist,p,t]);

subject to total_pkm_demand{p in PeriodStandard, t in Time[p]}:                    # peut-être pas utile finalement
sum{dist in Distances} Domestic_energy_pkm[dist,p,t] = Domestic_energy['Mobility',p,t];        # je pense qu'il manque quand même un paramètre t dans la borne supérieure, à moins que le profile de demande soit juste une quantité maximale de pkm sur une journée

# Travel Time
subject to travel_time_c1{p in Period,t in Time[p]}:
# travel_time[p,t] = sum{u in transport_Units : u != "Public_transport"}(Units_supply['Mobility',u,p,t] / Mode_Speed[u]) +( Network_supply['Mobility',p,t] / dp[p] / Mode_Speed['Public_transport']);
#travel_time[p,t] = sum{tu in transport_Units : substr(tu, 1, 2) != "PT"}(Units_supply['Mobility',tu,p,t]/Mode_Speed[tu]); # +(pkm_PT_bus[u,p,t]/Mode_Speed['PT_bus'] + pkm_PT_metro[u,p,t]/Mode_Speed['PT_metro']);   # + pkm_PT_train[u,p,t]/dp[p]/Mode_Speed['PT_train']
travel_time[p,t] = sum{tu in transport_Units}(Units_supply['Mobility',tu,p,t]/Mode_Speed[tu]);

subject to travel_time_c2{p in Period}:
sum {t in Time[p]}(travel_time[p,t]) <= max_travel_time * Population; 


# constraint on the max share of cars

subject to allcars_maxshare{p in PeriodStandard,dist in Distances}:
sum {u in transport_Units_cars, t in Time[p]}(pkm_supply[u,dist,p,t]) <= Population *  (DailyDist[dist] * max_share_modes['cars',dist] );

subject to allcars_minshare{p in PeriodStandard,dist in Distances}:
sum {u in transport_Units_cars, t in Time[p]}(pkm_supply[u,dist,p,t])  >=  Population *  (DailyDist[dist] * min_share_modes['cars',dist]);

subject to MD_maxshare{p in PeriodStandard,dist in Distances}:
sum {u in transport_Units_MD, t in Time[p]}(pkm_supply[u,dist,p,t]) <= Population *  (DailyDist[dist] * max_share_modes['MD',dist] );

subject to MD_minshare{p in PeriodStandard,dist in Distances}:
sum {u in transport_Units_MD, t in Time[p]}(pkm_supply[u,dist,p,t]) >= Population *  (DailyDist[dist] * min_share_modes['MD',dist] );

# Same for public transports just below

#--------------------------------------------------------------------------------------------------------------------#
#-PUBLIC TRANSPORTS
#--------------------------------------------------------------------------------------------------------------------#
# contraindre Network_supply avec un profil de capacité horaire
#-PARAMETERS
# param transport_public_capacity{p in Period, t in Time[p]} default 150; # pkm : availability of public transport each hour in pkm
param max_share_PT default 0.24; # [1] G 3.3.1.6 : share of trains amounts to ~ 20%
param min_share_PT default 0; # [1] G 3.3.1.6 : share of trains amounts to ~ 20%



#-CONSTRAINTS

subject to TP_maxshare{p in PeriodStandard,dist in Distances}:
sum {u in transport_Units_PT, t in Time[p]}(pkm_supply[u,dist,p,t])  <= Population * (DailyDist[dist] * max_share_modes['PT',dist] ); 

subject to TP_minshare{p in PeriodStandard,dist in Distances}:
sum {u in transport_Units_PT, t in Time[p]}(pkm_supply[u,dist,p,t])  >= Population * (DailyDist[dist] * min_share_modes['PT',dist]); 

# subject to TP_c1{u in UnitsOfType['EV'], p in Period, t in Time[p]}:
# pkm_PT_bus[u,p,t] <= Bus_demand_profile['EV_district',p,t];

# subject to TP_c1bis{u in UnitsOfType['EV'], p in Period, t in Time[p]}:
# pkm_PT_metro[u,p,t] <= Metro_demand_profile['EV_district',p,t];

# subject to TP_c2{u in UnitsOfType['EV'], p in Period, t in Time[p]}:      # plus besoin car on a Units_supply mtn
# Network_supply["Mobility",p,t]  = dp[p] * (pkm_PT_bus[u,p,t] + pkm_PT_metro[u,p,t]);  # pkm_PT_train[u,p,t] +

subject to TP_c3{u in UnitsOfType['PT_bus'] union UnitsOfType['PT_metro'], p in Period, t in Time[p]}:      # paramètre u ajouté pour correspondre à Units_demand
Units_demand["Mobility",u,p,t]  = 0;              # Network_demand transformé en Units_demand

# subject to TP_train_maxshare{u in UnitsOfType['EV'],p in PeriodStandard,dist in Distances}:
# #sum {t in Time[p]}(pkm_supply["PT_train",dist,p,t])<= max_share["PT_train",dist]* Population * DailyDist[dist];
# sum {t in Time[p]}(pkm_PT_train[u,p,t])/dp[p] <= max_share["PT_train",dist]* Population * DailyDist[dist];

subject to TP_bus_maxshare{u in UnitsOfType['PT_bus'],p in PeriodStandard,dist in Distances}:
#sum {t in Time[p]}(pkm_supply["PT_bus",dist,p,t])<= max_share["PT_bus",dist] * Population * DailyDist[dist];
#sum {t in Time[p]}(pkm_PT_bus[u,p,t]) <= max_share["PT_bus",dist] * Population * DailyDist[dist];
sum {t in Time[p]}(Units_supply["Mobility",u,p,t]) <= max_share["PT_bus",dist] * Population * DailyDist[dist];

subject to TP_metro_maxshare{u in UnitsOfType['PT_metro'],p in PeriodStandard,dist in Distances}:
#sum {t in Time[p]}(pkm_PT_metro[u,p,t]) <= max_share["PT_metro",dist] * Population * DailyDist[dist];
sum {t in Time[p]}(Units_supply["Mobility",u,p,t]) <= max_share["PT_metro",dist] * Population * DailyDist[dist];



# subject to TP_train_minshare{u in UnitsOfType['EV'],p in PeriodStandard,dist in Distances}:
# sum {t in Time[p]}(pkm_PT_train[u,p,t])/dp[p] >= min_share["PT_train",dist] * Population * DailyDist[dist];

subject to TP_bus_minshare{u in UnitsOfType['PT_bus'],p in PeriodStandard,dist in Distances}:
#sum {t in Time[p]}(pkm_PT_bus[u,p,t]) >= min_share["PT_bus",dist] * Population * DailyDist[dist];
sum {t in Time[p]}(Units_supply["Mobility",u,p,t]) >= min_share["PT_bus",dist] * Population * DailyDist[dist];

subject to TP_metro_minshare{u in UnitsOfType['PT_metro'],p in PeriodStandard,dist in Distances}:
sum {t in Time[p]}(Units_supply["Mobility",u,p,t]) >= min_share["PT_metro",dist] * Population * DailyDist[dist];

# subject to TP_maxshare_bis{dist in Distances, p in Period, t in Time[p]}:
# Network_supply["Mobility",p,t] <= Domestic_energy['Mobility',p,t];# * max_share_modes["PT", dist];