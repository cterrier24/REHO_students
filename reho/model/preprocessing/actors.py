from reho.paths import *
import pandas as pd
import numpy as np
import math
import sympy as sp

# TODO: add "statsmodels" and "sympy" in to env.
from scipy.optimize import curve_fit

import random

from collections import defaultdict

__doc__ = """
Generate maximum rental values
"""
def generate_renter_expense_max_new(qbuildings, income=None, rent_income_ratio = None):
    #TODO Change name and be Careful: per person or per household!
    renter_expense_max = []
    rent_percentage = pd.read_csv(os.path.join(path_to_actor, 'rent_proportion.csv'))
    income_thresholds_rent = rent_percentage["Income"].to_numpy() * 12
    if rent_income_ratio != None:
        rent_income_ratio =  np.array(rent_income_ratio)
    else:
        rent_income_ratio = rent_percentage["Percentage"].to_numpy()

    power_params, _ = curve_fit(power_law, income_thresholds_rent, rent_income_ratio)
    max_rent_pp = power_law(income, power_params[0], power_params[1]) * income
    for b in qbuildings["buildings_data"].keys():
        renter_expense_max.append(max_rent_pp * qbuildings["buildings_data"][b]['n_p'])
    return np.round(renter_expense_max, 0)

# define dagum function to model income distribution
def dagum_cdf(x, lambda_, delta, beta):
    return (1 + (x / lambda_)**-delta)**(-beta)

def dagum_inverse_cdf(u, lambda_, delta, beta):
    return lambda_ * ((1 / (u**(-1 / beta) - 1)))**(1 / delta)

def dagum_pdf(y, lambda_, delta, beta):
    x = sp.symbols('x')
    function = dagum_cdf(x, lambda_, delta, beta)
    derivative = sp.diff(function, x)
    f_derivative = sp.lambdify(x, derivative, 'numpy')
    return f_derivative(y)

def power_law(x, a, b):
    return (a * x ** b)

def get_actor_parameters(scenario, set_indexed, result, Scn_ID, Pareto_ID, iter = 0, h = str):
    params = {}
    for dual_variable in ['nu_Renters', 'nu_Owners','nu_ECM', 'nu_DSO']:
        dual_value = result[Scn_ID][Pareto_ID][iter - 1]['df_Actors_dual'][dual_variable]
        if dual_variable == 'nu_DSO' or dual_variable == 'nu_ECM':
            params[dual_variable] = dual_value.dropna()[0]
        else:
            params[dual_variable] = dual_value[h]

    if scenario["Objective"] == "TOTEX_actor":
        params["nu_" + set_indexed["ActorObjective"][0]] = 1.0

    owner_subsidies = result[Scn_ID][Pareto_ID][iter - 1]['df_District']['owner_subsidies']
    renter_subsidies = result[Scn_ID][Pareto_ID][iter - 1]['df_District']['renter_subsidies']
    ECM_subsidies = result[Scn_ID][Pareto_ID][iter - 1]['df_District']['ECM_subsidies']
    Costs_Unit_inv_district = result[Scn_ID][Pareto_ID][iter - 1]['df_Unit']['Costs_Unit_inv'].sum()
    C_renters_mobility = result[Scn_ID][Pareto_ID][iter - 1]['df_District']['C_renters_to_ECM_mobility']
    Costs_rep_district = result[Scn_ID][Pareto_ID][iter - 1]['df_Unit']['Costs_Unit_rep'].sum()
    DSO_reinforce = result[Scn_ID][Pareto_ID][iter - 1]['df_District']['DSO_reinforce']['Network']
    Cost_supply_district_mobility = result[Scn_ID][Pareto_ID][iter - 1]['df_District']['Cost_supply_district_mobility']

    params['owner_subsidies'] = owner_subsidies[h]
    params['renter_subsidies'] = renter_subsidies[h]
    params['ECM_subsidies'] = ECM_subsidies['Network']
    params['Costs_Unit_inv_district'] = Costs_Unit_inv_district
    params['Costs_rep_district'] = Costs_rep_district
    params['DSO_reinforce'] = DSO_reinforce
    params['C_renters_mobility'] = C_renters_mobility[h]
    params['Cost_supply_district_mobility'] = Cost_supply_district_mobility[h]

    lambdas = result[Scn_ID][Pareto_ID][iter - 1]["df_DW"]['lambda']
    df_sc_f = result[Scn_ID][Pareto_ID][iter - 1]["df_Actors_tariff_f"]["Cost_self_consumption"]["Electricity"]
    df_sc = df_sc_f * lambdas
    cost_self_consumption = df_sc.groupby(level=('Hub','Period','Time')).sum()
    params['Cost_self_consumption'] = cost_self_consumption[[h]]


    df_cost_supply = result[Scn_ID][Pareto_ID][iter - 1]["df_Actors_tariff"]["Cost_supply_district"]
    #cost_supply_district = df_cost_supply.groupby(level=('Hub', 'ResourceBalances','Period','Time')).sum()
    #params['Cost_supply_district'] = cost_supply_district[[h]]
    params['Cost_supply_district'] = df_cost_supply.xs(h,level='Hub',drop_level = False).swaplevel(0,1)

    df_cost_demand = result[Scn_ID][Pareto_ID][iter - 1]["df_Actors_tariff"]["Cost_demand_district"]
    params['Cost_demand_district'] = df_cost_demand.xs(h,level='Hub',drop_level = False).swaplevel(0,1)
    #df_cost_demand = df_cost_demand_f * lambdas
    #cost_demand_district = df_cost_demand.groupby(level=('Hub', 'ResourceBalances')).sum()
    #params['Cost_demand_district'] = cost_demand_district[[h]]

    return params

def get_actor_expenses(actor, building, last_MP_results=None, last_SP_results=None):
    last_MP_results = last_MP_results or {}
    last_SP_results = last_SP_results or {}

    # build self-consumption per building
    self_cons = {}
    for b, sp in last_SP_results.items():
        # assume sp['df_Unit_t'] and sp['df_Grid_t'] have MultiIndex: (Layer, Hub, Period, Time)
        prod = sp['df_Unit_t']['Units_supply']['Electricity'].sum()
        grid = sp['df_Grid_t']['Grid_demand']['Electricity'].sum()
        self_cons[b] = prod - grid

    # multiply by cost
    tariff_sc = last_MP_results['df_Actors_tariff']['Cost_self_consumption']['Electricity']
    cost_sc = {b: tariff_sc[b] * sc for b, sc in self_cons.items()}
    cost_sc_series = pd.Series(cost_sc)

    if actor.lower() == "renters":
        renter_expense = last_MP_results['df_District']['renter_expense'][building]
        renter_subsidies = last_MP_results['df_District']['renter_subsidies'][building]

        return renter_expense - renter_subsidies

    elif actor.lower() == "owner":
        owner_prof   = last_MP_results['df_District']['owner_profit'][building]
        owner_sub   =  last_MP_results['df_District']['owner_subsidies'][building]
        owner_inv   =  last_MP_results['df_District']['Costs_inv'][building]
        owner_pir_min   = last_MP_results['Samples']['Owner_PIR_min'].iloc[0,0]

        owner_exp = owner_prof + owner_sub #- owner_pir_min * owner_inv
        return owner_exp

    elif actor.lower() == "ecm":
        ECM_profit = last_MP_results['df_Actors_expense']['ECM_profit']['Network']
        ECM_subsidies = last_MP_results['df_District']['ECM_subsidies']['Network']
        return ECM_profit + ECM_subsidies

    elif actor.lower() == "dso":
        DSO_profit= last_MP_results['df_Actors_expense']['ECM_profit']['Network']
        return DSO_profit

    else:
        raise ValueError(f"Unknown actor: {actor}")

def get_self_consumption(unit_time_series, grid_time_series):
    unit_time_series_filtered = unit_time_series.xs('Electricity', level='Layer')
    grid_time_series_filtered = grid_time_series.xs('Electricity', level='Layer')
    rows = []

    feasible_solutions = unit_time_series_filtered.index.get_level_values('FeasibleSolution').unique()
    houses = unit_time_series_filtered.index.get_level_values('house').unique()
    periods = unit_time_series_filtered.index.get_level_values('Period').unique()

    for fs in feasible_solutions:
        for h in houses:
            for p in periods:
                try:
                    unit_df = unit_time_series_filtered.xs((fs, h, p), level=['FeasibleSolution', 'house', 'Period'])
                    grid_df = grid_time_series_filtered.xs((fs, h, p), level=['FeasibleSolution', 'house', 'Period'])
                except KeyError:
                    continue
                available_units = set(unit_df.index.get_level_values('Unit'))
                name_battery_10 = f'Battery_10_{h}'
                name_battery_100 = f'Battery_10_{h}'
                name_PV_20 = f'PV_20_{h}'
                name_PV_100 = f'PV_100_{h}'
                for t in grid_df.index:
                    try:
                        E_grid_demand = grid_df.loc[t, 'Grid_demand']
                        E_PV = unit_df.loc[(name_PV_20, t), 'Units_supply'] + unit_df.loc[(name_PV_100, t), 'Units_supply']
                        if name_battery_10 or name_battery_100 in available_units:
                            E_charging = unit_df.loc[(name_battery_10, t), 'Units_demand'] + unit_df.loc[(name_battery_100, t), 'Units_demand']
                            E_discharging = unit_df.loc[(name_battery_10, t), 'Units_supply'] + unit_df.loc[(name_battery_100, t), 'Units_supply']
                            sc = max(E_PV - E_charging + E_discharging - E_grid_demand, 0)
                        else:
                            sc = max(E_PV - E_grid_demand, 0)
                        rows.append((fs, h, p, t, sc))
                    except KeyError:
                        continue

    self_consumption = pd.DataFrame(rows, columns=['FeasibleSolution', 'House', 'Period', 'Time',
                                                             'Self_consumption'])
    self_consumption.set_index(['FeasibleSolution', 'House', 'Period', 'Time'], inplace=True)

    return self_consumption