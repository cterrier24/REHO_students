#####################################################################################################################
#--------------------------------------------------------------------------------------------------------------------#
# H2 storage tank
#--------------------------------------------------------------------------------------------------------------------#
######################################################################################################################

# Storage tank without any compression step considered


param H2_eff_ch{u in UnitsOfType['H2_storage']} 	default 0.7;			#-	[1]
param H2_eff_di{u in UnitsOfType['H2_storage']} 	default 0.7;			#-	[1]
param H2_limit_ch{u in UnitsOfType['H2_storage']} default 0.8;			#-	[2]
param H2_limit_di{u in UnitsOfType['H2_storage']} default 0.2;			#-	[1]
param H2_efficiency{u in UnitsOfType['H2_storage']} default 0.99992;		#-	[1]

var H2_E_stored{u in UnitsOfType['H2_storage'],p in Period,t in Time[p]} >= 0;

subject to H2_energy_balance{u in UnitsOfType['H2_storage'],p in Period,t in Time[p] diff {last(Time[p])}}:
(H2_E_stored[u,p,next(t,Time[p])] - H2_efficiency[u]*H2_E_stored[u,p,t]) = 
	( H2_eff_ch[u]*Units_demand['Hydrogen',u,p,t] - (1/H2_eff_di[u])*Units_supply['Hydrogen',u,p,t] )*dt[p];

#--SoC constraints
subject to H2_c1{u in UnitsOfType['H2_storage'],p in Period,t in Time[p]}:
H2_E_stored[u,p,t] <= H2_limit_ch[u]*Units_Mult[u];

subject to H2_c2{u in UnitsOfType['H2_storage'] ,p in Period,t in Time[p]}:
H2_E_stored[u,p,t] >= H2_limit_di[u]*Units_Mult[u];

subject to H2_c3{u in UnitsOfType['H2_storage'] ,p in Period,t in Time[p]}:
Units_demand['Hydrogen',u,p,t]*dt[p] <= (H2_limit_ch[u]-H2_limit_di[u])*Units_Mult[u];

subject to H2_c4{u in UnitsOfType['H2_storage'],p in Period,t in Time[p]}:
Units_supply['Hydrogen',u,p,t]*dt[p] <= (H2_limit_ch[u]-H2_limit_di[u])*Units_Mult[u];
																										
#--Cyclic
subject to H2_EB_cyclic1{u in UnitsOfType['H2_storage'],p in Period}:
(H2_E_stored[u,p,first(Time[p])] - H2_efficiency[u]*H2_E_stored[u,p,last(Time[p])]) =
	(H2_eff_ch[u]*Units_demand['Hydrogen',u,p,last(Time[p])] - (1/H2_eff_di[u])*Units_supply['Hydrogen',u,p,last(Time[p])])*dt[p];
