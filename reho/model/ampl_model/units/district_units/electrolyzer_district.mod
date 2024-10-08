#####################################################################################################################
#--------------------------------------------------------------------------------------------------------------------#
# Electrolyzer
#--------------------------------------------------------------------------------------------------------------------#
######################################################################################################################

param ETZ_conv_eff_basis{u in UnitsOfType['Electrolyzer']} >=0, <=1 default 0.76; # elec to H2 LHV eff : (H2 LHV/elec)
param ETZ_partload_max{u in UnitsOfType['Electrolyzer']} default 1;
param ETZ_partload_min{u in UnitsOfType['Electrolyzer']} default 0.3;


subject to ETZ_energy_balance_1{u in UnitsOfType['Electrolyzer'],p in Period,t in Time[p]}:
Units_supply['Hydrogen',u,p,t] 	= ETZ_conv_eff_basis[u]*Units_demand['Electricity',u,p,t];

subject to ETZ_c1{u in UnitsOfType['Electrolyzer'],p in Period,t in Time[p]}:
Units_supply['Hydrogen',u,p,t] <= Units_Mult[u]*ETZ_partload_max[u];

subject to ETZ_c2{u in UnitsOfType['Electrolyzer'],p in Period,t in Time[p]}:
Units_supply['Hydrogen',u,p,t] >= Units_Mult[u]*ETZ_partload_min[u];
