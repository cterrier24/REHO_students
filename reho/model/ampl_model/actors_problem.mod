set Actors default {"Owners", "Renters", "ECM", "DSO"};
set ActorObjective;

# Energy tariffs
var Cost_supply_district{l in ResourceBalances, f in FeasibleSolutions, h in House, p in Period,t in Time[p]};
var Cost_demand_district{l in ResourceBalances, f in FeasibleSolutions, h in House, p in Period,t in Time[p]};
var Cost_self_consumption{f in FeasibleSolutions, h in House, p in Period,t in Time[p]};

subject to size_cstr1{l in ResourceBalances, f in FeasibleSolutions, h in House, p in Period,t in Time[p]}:            
   Cost_demand_cst[l] *lambda[f,h] <= Cost_supply_district[l,f,h,p,t];

subject to size_cstr2{l in ResourceBalances, f in FeasibleSolutions, h in House, p in Period,t in Time[p]}:            
   Cost_supply_district[l,f,h,p,t] <= Cost_supply_cst[l] *lambda[f,h];

subject to size_cstr3{l in ResourceBalances, f in FeasibleSolutions, h in House, p in Period,t in Time[p]}:            
   Cost_demand_cst[l] * lambda[f,h] <= Cost_demand_district[l,f,h,p,t];

subject to size_cstr4{l in ResourceBalances, f in FeasibleSolutions, h in House, p in Period,t in Time[p]}:           
   Cost_demand_district[l,f,h,p,t] <= Cost_supply_cst[l] *lambda[f,h];

subject to size_cstr5{l in ResourceBalances, f in FeasibleSolutions, h in House, p in Period,t in Time[p]: l="Electricity"}:            
   Cost_demand_cst[l] *lambda[f,h] <= Cost_self_consumption[f,h,p,t];

subject to size_cstr6{l in ResourceBalances, f in FeasibleSolutions, h in House, p in Period,t in Time[p]: l="Electricity"}:           
   Cost_self_consumption[f,h,p,t] <= Cost_supply_cst[l] *lambda[f,h];

#subject to uniform_price1{l in ResourceBalances, h in House,p in Period,t in Time[p], b in House: h!=b}:
#   sum{f in FeasibleSolutions} Cost_supply_district[l,f,h,p,t] = sum{f in FeasibleSolutions} Cost_supply_district[l,f,b,p,t]; 

#subject to uniform_price2{l in ResourceBalances, h in House,p in Period,t in Time[p], b in House: h!=b}:
#   sum{f in FeasibleSolutions} Cost_demand_district[l,f,h,p,t] = sum{f in FeasibleSolutions} Cost_demand_district[l,f,b,p,t]; 

#subject to uniform_price3{h in House,p in Period,t in Time[p], b in House: h!=b}:
#   sum{f in FeasibleSolutions} Cost_self_consumption[f,h,p,t] = sum{f in FeasibleSolutions} Cost_self_consumption[f,b,p,t] ; 

# Self-consumption
param PV_prod{f in FeasibleSolutions, h in House, p in Period, t in Time[p]};
param PV_self_consummed{f in FeasibleSolutions, h in House, p in Period, t in Time[p]} :=  PV_prod[f,h,p,t] - Grid_demand["Electricity",f,h,p,t];

#--------------------------------------------------------------------------------------------------------------------#
# Renters constraints
#--------------------------------------------------------------------------------------------------------------------#
var objective_functions{a in Actors};

param renter_expense_max{h in House} default 1e10; 
var renter_expense{h in House};
var C_op_renters_to_ECM{h in House} >= 0;
var C_op_renters_to_owners{h in House} >= 0;

subject to Costs_opex_renter_ECM{h in House}:
C_op_renters_to_ECM[h] = sum{l in ResourceBalances, f in FeasibleSolutions, p in PeriodStandard, t in Time[p]} (Cost_supply_district[l,f,h,p,t]* Grid_supply[l,f,h,p,t] * dp[p] * dt[p]);

subject to Costs_opex_renter_owner{h in House}:
C_op_renters_to_owners[h] = sum{f in FeasibleSolutions, p in PeriodStandard, t in Time[p]} (Cost_self_consumption[f,h,p,t] * PV_self_consummed[f,h,p,t] * dp[p] * dt[p]);

subject to Renter_expense_calc{h in House}:
renter_expense[h] = C_op_renters_to_ECM[h] + C_op_renters_to_owners[h];

subject to Renter_noSub{h in House}:
renter_subsidies[h] = 0;

subject to Renter_epsilon{h in House}: #nu_renters
renter_expense[h] - renter_subsidies[h] <= (41-15.3) * ERA[h]; #renter_expense_max[h];

subject to obj_fct1:
objective_functions["Renters"] = sum{h in House}(renter_expense[h]);

#--------------------------------------------------------------------------------------------------------------------#
# Owners constraints
#--------------------------------------------------------------------------------------------------------------------#
param owner_PIR_min default 0;
param owner_PIR_max default 0.3;

var C_op_owners_to_ECM{h in House};
var C_op_ECM_to_owners{h in House};

var owner_profit{h in House};

param Uh{h in House} default 0;
param Uh_ins{f in FeasibleSolutions,h in House} default 0;
param ins_target default 0;
var is_ins{h in House} binary; 

subject to Insulation_rate:
sum{h in House} (is_ins[h] * ERA[h]) >= ins_target * sum{h in House} (ERA[h]);

var renovation{h in House};

subject to Insulation1{h in House}:
Uh[h] - sum{f in FeasibleSolutions}(Uh_ins[f,h] * lambda[f,h])  >= 0.000009 - 10000 * (1 - is_ins[h]);
subject to Insulation2{h in House}:
Uh[h] - sum{f in FeasibleSolutions}(Uh_ins[f,h] * lambda[f,h]) <= 0.000009 + 10000 * is_ins[h];

subject to Owner_Link_Subsidy_to_Insulation{h in House}:
owner_subsidies[h] <= 1e10 * is_ins[h];

subject to Owner_grid_connection{h in House}:
C_op_owners_to_ECM[h] = sum{l in ResourceBalances} Costs_grid_connection_House[l,h];

subject to Owner_profit_calc{h in House}:
owner_profit[h] = C_op_renters_to_owners[h] + C_op_ECM_to_owners[h] - C_op_owners_to_ECM[h] - Costs_House_inv[h];

subject to Owner_epsilon{h in House}: 
owner_profit[h] + owner_subsidies[h] >= 0 ; #owner_PIR_min * Costs_House_inv[h];

subject to Owner_noSub{h in House}:
owner_subsidies[h] = 0;

subject to obj_fct2:
objective_functions["Owners"] = - sum{h in House}(owner_profit[h]);

#--------------------------------------------------------------------------------------------------------------------#
# ECM constraints
#--------------------------------------------------------------------------------------------------------------------#
param ECM_profit_min default -1e-6;
var ECM_profit;
var C_op_ECM_to_DSO;

subject to ECM{h in House}: 
C_op_ECM_to_owners[h] = sum{l in ResourceBalances, f in FeasibleSolutions, p in PeriodStandard, t in Time[p]} (Cost_demand_district[l,f,h,p,t] * Grid_demand[l,f,h,p,t] * dp[p] * dt[p]);

subject to ECM2:
C_op_ECM_to_DSO = sum{p in PeriodStandard, t in Time[p]}(0.35 * (Cost_supply_network["Electricity",p,t] * Network_supply["Electricity",p,t] + Cost_demand_network["Electricity",p,t] * Network_demand["Electricity",p,t])) 
                     + 0.02 * sum{h in House, f in FeasibleSolutions, p in PeriodStandard, t in Time[p]}(lambda[f,h] * Grid_demand["Electricity",f,h,p,t] * dp[p] * dt[p]); 

subject to ECM_profit_calc:
ECM_profit = sum{h in House} (C_op_renters_to_ECM[h] + C_op_owners_to_ECM[h] - C_op_ECM_to_owners[h]) - C_op_ECM_to_DSO - Costs_op - tau * sum{u in Units} (Costs_Unit_inv[u] - Costs_rep);

subject to ECM_epsilon:
ECM_profit + ECM_subsidies >= ECM_profit_min;

subject to obj_fct3:
objective_functions["ECM"] = - ECM_profit;


#--------------------------------------------------------------------------------------------------------------------#
# Distribution System Operator (DSO)
#--------------------------------------------------------------------------------------------------------------------#
var DSO_profit;
var DSO_reinforce;
param DSO_profit_min default -1e-6;

subject to DSO_expense: 
DSO_reinforce = sum{l in ResourceBalances} (Cost_network_inv1[l]*Use_Network_capacity[l]+Cost_network_inv2[l] * (Network_capacity[l]-Network_ext[l] * (1- Use_Network_capacity[l])));

subject to DSO_profit_calc:
DSO_profit =  C_op_ECM_to_DSO - tau * DSO_reinforce;

subject to DSO_epsilon:
DSO_profit >= DSO_profit_min; 

subject to obj_fct4:
objective_functions["DSO"] = - DSO_profit;

#--------------------------------------------------------------------------------------------------------------------#
# Objectives
#--------------------------------------------------------------------------------------------------------------------#
minimize TOTEX_actor:
sum {a in ActorObjective} objective_functions[a] + penalty_ratio * (Costs_inv + Costs_op + sum{h in House}(renter_subsidies[h] + owner_subsidies[h]) + ECM_subsidies);
