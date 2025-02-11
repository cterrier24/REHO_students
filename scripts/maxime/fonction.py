######################################################################################################################################
#### File with multiple functions to plot all the graphs regarding electricity : total or mobility consumption, PV production,    ####
#### EV-stored electricity and final grid consumption. You cna also find the functions to other relevant plots such as populaiton ####
#### or modal shares evolution, connectivity distribution, EV and bus charging profiles.                                          ####
#### When relevant, the functions offer the possibility of choosing the typical period, the year, the scenario (PVHP or not),     ####
#### plotting the district's capacity and even select the result files corresponding to the limitation of the transformer's       #### 
#### capacity if modelled via the capacity_lim argument (not considered in the thesis)                                            ####
######################################################################################################################################


import csv
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd
import geopandas as gpd
import seaborn as sns
import numpy as np
from mobility_demand_plot import weekdays, weekends
from matplotlib.colors import to_rgba, to_hex


def generate_bus_charging_profile():
    '''
    cf note méthodo pour le détail de la répartition des recharges
    '''
    t = [time for time in range(24)]
    charging_profile = [0]*24
    csv_dir = "../../reho/data/mobility/"

    # recharge de nuit
    for i in range(1,6):
        charging_profile[i] = 445/5             # batterie de 445 kWh et 5h de charge supposée uniforme

    # recharge aux terminus
    charging_profile[0] = 30*2
    for j in range(6,24):
        charging_profile[j] = 30*2              # 20' de trajet + 10' de recharge (de 30 kWh), on a deux recharges par heure


    # enregistrer dans un csv
    data = [[time] + [chg] for time,chg in zip(t,charging_profile)]
    with open(f"{csv_dir}ebus_chgpf.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['t','kWh'])
        writer.writerows(data)

    # afficher le graphique
    plt.plot(t, charging_profile)
    plt.xlabel('t (hours)')
    plt.ylabel('Electric consumption (kW)')
    plt.ylim([0,100])
    plt.grid(True)
    plt.savefig('figure/ebus_chargingprofile.png')
    plt.show()


def connectivity_plot():
    gdf = gpd.read_file('data/transfo_lausanne_connectivity.gpkg')
    result = pd.read_pickle("data/mixture_LAU_9.pickle")
    id = result["Best iter id"]
    cluster_list = result['typical districts id'].iloc[id]
    cluster_list.iloc[5] = 3216
    # result_class = pd.read_pickle("data/mixture_LAU_9_class.pickle")
    # id_class = result_class["Best iter id"]
    # cluster_list_class = result_class['typical districts id'].iloc[id_class]

    connec_value = gdf['connectivity level']
    connec_typical_value = [0]*len(cluster_list)
    for i, x in enumerate(cluster_list):
        # if x == 10491:
        #     x = 3216
        connec_typical_value[i] = result['Data'][result['Data']['id']==x]['connectivity level']
        connec_typical_value[i] = connec_typical_value[i].values[0]
    connec_typical_value.sort()
    print("connectivity", connec_typical_value)
    stat_data = [np.mean(connec_value),np.median(connec_value)]
    stat_label = ['mean','median']
    print("stats", stat_data)

    # connec_typical_value_class = [0]*len(cluster_list_class)
    # for i,x in enumerate(cluster_list_class):
    #     connec_typical_value_class[i] = result['Data'][result['Data']['id']==x]['connectivity level']
    #     connec_typical_value_class[i] = connec_typical_value_class[i].values[0]

    # KDE (courbe de densité) globale
    plt.figure(figsize=(8, 5))
    sns.kdeplot(connec_value, fill=True, color='purple')
    for i in range(len(connec_typical_value)):
        plt.axvline(x=connec_typical_value[i], color='red', linestyle='dashed', label='_nolegend_')
        # plt.axvline(x=connec_typical_value_class[i], color='royalblue', linestyle='dotted', label='_nolegend_')
        if connec_typical_value[i] < 0.75:
            plt.text(connec_typical_value[i], 0.1, f'#{i+1}', rotation=45, color='red')
        # if connec_typical_value_class[i] < 0.75:
        #     plt.text(connec_typical_value_class[i], 0.8, '', rotation=45, color='royalblue')
    for j in range(len(stat_data)):
        plt.axvline(x=stat_data[j], color='darkviolet', linestyle='dashdot', label='_nolegend_')
        #plt.axvline(x=stat_data_class[j], color='navy', linestyle=':')
        plt.text(stat_data[j], 0.3, f'{stat_label[j]}', rotation=45, color='darkviolet')
        #plt.text(stat_data_class[j], 0.7, f'{stat_label[j]}', rotation=45, color='navy')
    plt.xlim([0,1])
    legend = [Line2D([0], [0], color='red', linestyle='dashed', label='Typical districts'),
              #Line2D([0], [0], color='royalblue', linestyle='dotted', label='Clustering w/o connectivity'),
              Line2D([0], [0], color='darkviolet', linestyle='dashdot', label='Statistical values'),
              Line2D([0], [0], color='purple', linestyle='-', label='KDE'),]
    plt.legend(handles=legend, loc='upper left')
    plt.title('Kernel Density Estimation (KDE)')
    plt.xlabel('Connectivity level')
    plt.ylabel('Density')
    plt.savefig('figure/connectivity plot/KDE_globale.png')
    plt.tight_layout()
    plt.show()


    # KDE (courbe de densité) zoomée
    plt.figure(figsize=(8, 5))
    sns.kdeplot(connec_value, fill=True, color='purple')
    for i in range(len(connec_typical_value)):
        plt.axvline(x=connec_typical_value[i], color='red', linestyle='dashed', label='_nolegend_')
        #plt.axvline(x=connec_typical_value_class[i], color='royalblue', linestyle='dotted', label='_nolegend_')
        if connec_typical_value[i] >= 0.8:
            plt.text(connec_typical_value[i], 0.1, f'#{i+1}', rotation=45, color='red')
        # if connec_typical_value_class[i] >= 0.75:
        #     plt.text(connec_typical_value_class[i], 0.8, '', rotation=45, color='royalblue')
    for j in range(len(stat_data)):
        plt.axvline(x=stat_data[j], color='darkviolet', linestyle='dashdot', label='_nolegend_')
        #plt.axvline(x=stat_data_class[j], color='navy', linestyle=':')
        plt.text(stat_data[j], 0.3, f'{stat_label[j]}', rotation=45, color='darkviolet')
        #plt.text(stat_data_class[j], 0.7, f'{stat_label[j]}', rotation=45, color='navy')
    plt.xlim([0.8,1])
    plt.legend(handles=legend, loc='upper right')
    plt.title('Kernel Density Estimation (KDE)')
    plt.xlabel('Connectivity level')
    plt.ylabel('Density')
    plt.savefig('figure/connectivity plot/KDE_zoom.png')
    plt.show()


def transformer_capacity(transformer,file):
    if np.isnan(transformer):
        result = file
        df_building_t = result['capex'][0]['df_Buildings_t']
    else:
        result = pd.read_pickle(f"../examples/results/{transformer}/baseline/7o_{transformer}.pickle")
        df_building_t = result['totex_0'][0]['df_Buildings_t']

    capacity = 0
    # for i in range(len(df_building_t.index.get_level_values('Hub').unique())):
    #     peak_list = []
    #     for p in range(10):
    #         peak = df_building_t.xs(f'Building{i+1}', level='Hub').xs(p+1, level='Period')['Domestic_electricity'].max()
    #         peak_list.append(peak)
    #         #print(f'Building{i}', peak_list)
    #     capacity += max(peak_list)

    peaklist = []
    for p in range(10):
        p_cons = df_building_t.xs(f'Building1', level='Hub').xs(p+1, level='Period')['Domestic_electricity']
        for i in range(1,len(df_building_t.index.get_level_values('Hub').unique())):
            p_cons += df_building_t.xs(f'Building{i+1}', level='Hub').xs(p+1, level='Period')['Domestic_electricity']
        peaklist.append(p_cons.max())
    
    return max(peaklist)


## Plots the mobility-related electricity consumption
def plot_grid_supply_mob(year, transformer, plot_capacity=False, pvhp=True):
    t = np.arange(1,25,1)

    # if not pvhp:
    #     df = pd.read_pickle(f'../examples/results/{transformer}/{year}/noPVHP/7a_{transformer}_{year}_no_PVHP.pickle')
    # else:
    #     df = pd.read_pickle(f'../examples/results/{transformer}/{year}/7a_{transformer}_{year}.pickle')

    #df = pd.read_pickle(f'../examples/results/{transformer}/{year}/7a_{transformer}.pickle')
    #df = pd.read_pickle(f'../examples/results/{transformer}/{year}/7a_{transformer}_{year}.pickle')
    df = pd.read_pickle(f'../examples/results/7a_{transformer}_{year}_fix.pickle')
    working_df = df['totex'][0]['df_Unit_t'].xs('Electricity', level='Layer')

    E_trolley = dict()
    E_ebus = dict()
    E_metro = dict()
    E_EV_charger = dict()
    E_EV_supply = dict()

    for p in range(1,11):
        E_trolley[p] = 24*[0]
        E_ebus[p] = 24*[0]
        E_metro[p] = 24*[0]
        E_EV_charger[p] = 24*[0]
        E_EV_supply[p] = 24*[0]


    for p in range(1,11):
        E_trolley[p] = working_df.xs('TrolleyBus_district', level='Unit').xs(p, level='Period')['trolley_demand']
        E_ebus[p] = working_df.xs('ElectricBus_district', level='Unit').xs(p, level='Period')['ebus_demand']
        E_metro[p] = working_df.xs('Metro_district', level='Unit').xs(p, level='Period')['metro_demand']
        E_EV_charger[p] = working_df.xs('EV_charger_district', level='Unit').xs(p, level='Period')['Units_demand']
        E_EV_supply[p] = working_df.xs('EV_charger_district', level='Unit').xs(p, level='Period')['Units_supply']
        

    # color creation for plotting
    base_color_mob = to_rgba('navy', alpha=0.6)
    #label_mob = ['Trolleybus', 'Electric bus', 'Metro', 'EV supply', 'EV chargers']
    label_mob = ['Trolleybus', 'Electric bus', 'Metro', 'EV chargers']
    colors_mob = generate_shades(base_color_mob, len(label_mob))

    for p in range(1,11):
        #data_to_plot = np.array([E_trolley[p], E_ebus[p], E_metro[p], E_EV_supply[p], E_EV_charger[p]-E_EV_supply[p]])
        data_to_plot = np.array([E_trolley[p], E_ebus[p], E_metro[p], E_EV_charger[p]])

        plt.figure(figsize=(8, 5))
        plt.stackplot(t, data_to_plot, colors=colors_mob)
        for i, (data,color) in enumerate(zip(data_to_plot,colors_mob)):
            if np.any(data):
                plt.plot([], [], label=label_mob[i], color=color)
        if plot_capacity:
            capacity = 3*transformer_capacity(transformer,np.nan)
            plt.axhline(capacity, color='purple', linestyle='dotted', label='Transformer maximum capacity')

        plt.xlabel('t (hours)')
        plt.ylabel('Electricity consumption from the grid (kW)')
        plt.legend()
        plt.grid()

        plt.title(f'{transformer} - {year} - Period {p}')
        # if pvhp:
        #     if plot_capacity:
        #         plt.savefig(f'figure/{transformer}/{year}/elec/grid_supply_capacity_mob/grid_supply_capacity_mob_{p}.png')
        #     else:
        #         plt.savefig(f'figure/{transformer}/{year}/elec/grid_supply_mob/grid_supply_mob_{p}.png')
        # else:
        #     if plot_capacity:
        #         plt.savefig(f'figure/{transformer}/{year}/noPVHP/elec/grid_supply_capacity_mob/grid_supply_capacity_mob_{p}.png')
        #     else:
        #         plt.savefig(f'figure/{transformer}/{year}/noPVHP/elec/grid_supply_mob/grid_supply_mob_{p}.png')
        

        plt.tight_layout()
        plt.show()


## Plots the total electricity consumption
def plot_grid_supply_total(year, transformer, plot_capacity=False, capacity_lim=False, pvhp=True):
    t = np.arange(1,25,1)
    #df = pd.read_pickle(f'../examples/results/{transformer}/{year}/7a_{transformer}_{year}_relax_0.3.pickle')
    df = pd.read_pickle(f'../examples/results/{transformer}/fix/7a_{transformer}_{year}_fix_relax.pickle')

    # if not pvhp:
    #     df = pd.read_pickle(f'../examples/results/{transformer}/{year}/noPVHP/7a_{transformer}_{year}_no_PVHP.pickle')
    # else:
    #     df = pd.read_pickle(f'../examples/results/{transformer}/{year}/7a_{transformer}_{year}.pickle')

    # if capacity_lim:
    #     df = pd.read_pickle(f'../examples/results/{transformer}/{year}/7a_{transformer}_{year}_cap.pickle')
    # else:
    #     #df = pd.read_pickle(f'../examples/results/7a_{transformer}_{year}_cap.pickle')
    #     df = pd.read_pickle(f'../examples/results/{transformer}/{year}/7a_{transformer}_{year}.pickle')
    df_building_t = df['totex'][0]['df_Buildings_t']
    working_df = df['totex'][0]['df_Unit_t'].xs('Electricity', level='Layer')

    # mobility electricity consumption
    E_trolley = dict()
    E_ebus = dict()
    E_metro = dict()
    E_EV_charger = dict()

    # buildings electricity consumption
    E_AC = dict()
    E_EH_dhw = dict()
    E_EH_sh = dict()
    E_HP_a = dict()
    E_HP_geo = dict()
    E_dom_elec = dict()

    for p in range(1,11):
        E_trolley[p] = 24*[0]
        E_ebus[p] = 24*[0]
        E_metro[p] = 24*[0]
        E_EV_charger[p] = 24*[0]
        E_AC[p] = 24*[0]
        E_EH_dhw[p] = 24*[0]
        E_EH_sh[p] = 24*[0]
        E_HP_a[p] = 24*[0]
        E_HP_geo[p] = 24*[0]
        E_dom_elec[p] = 24*[0]

    # iteration for housing
    for i in range(len(df_building_t.index.get_level_values('Hub').unique())):
        for p in range(1,11):
            E_AC[p] += round(working_df.xs(f'Air_Conditioner_Air_Building{i+1}', level='Unit').xs(p, level='Period')['Units_demand'],3)
            E_EH_dhw[p] += round(working_df.xs(f'ElectricalHeater_DHW_Building{i+1}', level='Unit').xs(p, level='Period')['Units_demand'],3)
            E_EH_sh[p] += round(working_df.xs(f'ElectricalHeater_SH_Building{i+1}', level='Unit').xs(p, level='Period')['Units_demand'],3)
            E_HP_a[p] += round(working_df.xs(f'HeatPump_Air_Building{i+1}', level='Unit').xs(p, level='Period')['Units_demand'],3)
            E_HP_geo[p] += round(working_df.xs(f'HeatPump_Geothermal_Building{i+1}', level='Unit').xs(p, level='Period')['Units_demand'],3)
            E_dom_elec[p] += round(df_building_t.xs(f'Building{i+1}', level='Hub').xs(p, level='Period')['Domestic_electricity'],3)

    # iteration over mobility only
    for p in range(1,11):
        E_trolley[p] = working_df.xs('TrolleyBus_district', level='Unit').xs(p, level='Period')['trolley_demand']
        E_ebus[p] = working_df.xs('ElectricBus_district', level='Unit').xs(p, level='Period')['ebus_demand']
        E_metro[p] = working_df.xs('Metro_district', level='Unit').xs(p, level='Period')['metro_demand']
        E_EV_charger[p] = working_df.xs('EV_charger_district', level='Unit').xs(p, level='Period')['Units_demand']
            
    
    # color creation for plotting
    base_color_mob = to_rgba('navy', alpha=0.8)
    base_color_housing = to_rgba('orange', alpha=0.8)

    label_mob = ['Rest of mobility', 'EV chargers']
    label_housing = ['Air Conditioner', 'Heat Pump', 'Domestic electricity']

    colors_mob = generate_shades(base_color_mob, len(label_mob))
    colors_housing = generate_shades(base_color_housing, len(label_housing))


    for p in range(1,11):
        E_mob_rest = [tro+bus+met for tro,bus,met in zip(E_trolley[p],E_ebus[p],E_metro[p])]
        E_EH = [dhw+sh for dhw,sh in zip(E_EH_dhw[p],E_EH_sh[p])]
        E_HP = [a+geo for a,geo in zip(E_HP_a[p],E_HP_geo[p])]

        E_mob = np.array([E_mob_rest, E_EV_charger[p]])
        E_housing = np.array([E_AC[p], E_HP, E_dom_elec[p]])
        data_to_plot = np.array([E_mob_rest, E_EV_charger[p], E_AC[p], E_HP, E_dom_elec[p]])

        plt.figure(figsize=(8, 5))
        plt.stackplot(t, data_to_plot, colors=colors_mob+colors_housing)
        for i, (data,color) in enumerate(zip(E_mob,colors_mob)):
            if np.any(data):
                plt.plot([], [], label=label_mob[i], color=color)
        for i, (data,color) in enumerate(zip(E_housing,colors_housing)):
            if np.any(data):
                plt.plot([], [], label=label_housing[i], color=color)
        if plot_capacity:
            capacity = 3*transformer_capacity(transformer,np.nan)
            plt.axhline(capacity, color='purple', linestyle='dotted', label='Transformer maximum capacity')

        plt.xlabel('t (hours)')
        plt.ylabel('Total electricity consumption (kW)')
        plt.legend()
        plt.grid()

        
        plt.title(f'{transformer} - {year} - Period {p}')
        # if plot_capacity and capacity_lim:
        #     plt.savefig(f'figure/{transformer}/{year}/capacity_lim/grid_supply_capacity_total_{p}_lim.png')
        # elif plot_capacity and not capacity_lim:
        #     plt.savefig(f'figure/{transformer}/{year}/elec/grid_supply_capacity_total/grid_supply_capacity_total_{p}.png')
        # elif capacity_lim and not plot_capacity :
        #     plt.savefig(f'figure/{transformer}/{year}/capacity_lim/grid_supply_total_{p}_lim.png')
        # elif not capacity_lim and not plot_capacity:
        #     plt.savefig(f'figure/{transformer}/{year}/elec/grid_supply_capacity_total/grid_supply_total_{p}_lim.png')
        
        # if pvhp:
        #     plt.savefig(f'figure/{transformer}/{year}/elec/grid_supply_capacity_total/grid_supply_capacity_total_{p}.png')
        # else:
        #     plt.savefig(f'figure/{transformer}/{year}/noPVHP/elec/grid_supply_capacity_total/grid_supply_capacity_total_{p}.png')
        #plt.savefig(f'figure/{transformer}/{year}/relaxation/grid_supply_capacity_total/grid_supply_capacity_total_{p}.png')
        plt.savefig(f'figure/{transformer}/fix/relax/total_grid_cons/total_grid_cons_{p}_{year}_relax.png')

        plt.tight_layout()
        plt.show()


## Plots the electricity produced from outside-the-grid sources (PV and EVs)
def plot_elec_ext(year, transformer, plot_capacity=False, capacity_lim=False, pvhp=True):
    t = np.arange(1,25,1)
    df = pd.read_pickle(f'../examples/results/{transformer}/fix/7a_{transformer}_{year}_fix_relax.pickle')  

    # if not pvhp:
    #     df = pd.read_pickle(f'../examples/results/{transformer}/{year}/noPVHP/7a_{transformer}_{year}_no_PVHP.pickle')
    # else:
    #     df = pd.read_pickle(f'../examples/results/{transformer}/{year}/7a_{transformer}_{year}.pickle')

    # if capacity_lim:
    #     df = pd.read_pickle(f'../examples/results/{transformer}/{year}/7a_{transformer}_{year}_cap.pickle')
    # else:
    #     #df = pd.read_pickle(f'../examples/results/7a_{transformer}_{year}_sankey.pickle')
    #     df = pd.read_pickle(f'../examples/results/{transformer}/{year}/7a_{transformer}_{year}.pickle')
    df_building_t = df['totex'][0]['df_Buildings_t']
    working_df = df['totex'][0]['df_Unit_t'].xs('Electricity', level='Layer')
    working_df_grid = df['totex'][0]['df_Grid_t'].xs('Electricity', level='Layer')

    E_PV = dict()
    E_PV_export = dict()
    E_battery = dict()
    E_EV = dict()
    for p in range(1,11):
        E_PV[p] = 24*[0]
        E_PV_export[p] = 24*[0]
        E_battery[p] = 24*[0]
        E_EV[p] = 24*[0]
        

    for p in range(1,11):
        E_EV[p] = working_df.xs('EV_charger_district', level='Unit').xs(p, level='Period')['Units_supply']
        E_PV_export[p] = round(working_df_grid.xs('Network', level='Hub').xs(p, level='Period')['Grid_demand'],3)
        for i in range(len(df_building_t.index.get_level_values('Hub').unique())):
            E_PV[p] += round(working_df.xs(f'PV_Building{i+1}', level='Unit').xs(p, level='Period')['Units_supply'],3)
            E_battery[p] += round(working_df.xs(f'Battery_Building{i+1}', level='Unit').xs(p, level='Period')['Units_demand'],3)


    base_color = to_rgba('gold', alpha=0.6)
    label_mob = ['PV (consumption)', 'PV (export)', 'EV', 'Battery']
    colors = generate_shades(base_color, len(label_mob))

    for p in range(1,11):
        data_to_plot = np.array([E_PV[p]-E_PV_export[p], E_PV_export[p],  E_EV[p], E_battery[p]])

        plt.figure(figsize=(8, 5))
        #plt.plot(t, E_battery[p])
        plt.stackplot(t, data_to_plot, colors=colors)
        for i, (data,color) in enumerate(zip(data_to_plot,colors)):
            if np.any(data):
                plt.plot([], [], label=label_mob[i], color=color)
        if plot_capacity:
            capacity = 3*transformer_capacity(transformer,np.nan)
            plt.axhline(capacity, color='purple', linestyle='dotted', label='Transformer maximum capacity')

        plt.xlabel('t (hours)')
        plt.ylabel('Electricity consumption outside the grid grid (kW)')
        plt.legend()
        plt.grid()
        
        plt.title(f'{transformer} - {year} - Period {p}')
        # if plot_capacity and capacity_lim:
        #     plt.savefig(f'figure/{transformer}/{year}/capacity_lim/ext_supply_capacity_total_{p}_lim.png')
        # elif plot_capacity and not capacity_lim:
        #     plt.savefig(f'figure/{transformer}/{year}/elec/ext_supply/ext_supply_capacity_total_{p}.png')
        # elif capacity_lim and not plot_capacity :
        #     plt.savefig(f'figure/{transformer}/{year}/capacity_lim/ext_supply_total_{p}_lim.png')
        # elif not capacity_lim and not plot_capacity:
        #     plt.savefig(f'figure/{transformer}/{year}/elec/ext_supply/ext_supply_total_{p}_lim.png')

        # if pvhp:
        #     plt.savefig(f'figure/{transformer}/{year}/elec/ext_supply/ext_supply_capacity_total_{p}.png')
        # else:
        #     plt.savefig(f'figure/{transformer}/{year}/noPVHP/elec/ext_supply/ext_supply_total_{p}.png')
        #plt.savefig(f'figure/{transformer}/{year}/relaxation/ext_supply/ext_supply_total_{p}.png')
        plt.savefig(f'figure/{transformer}/fix/relax/ext_supply/ext_supply_{p}_{year}_relax.png')

        plt.tight_layout()
        plt.show()


## Function that generates shades of color for plot_grid_supply_total()
def generate_shades(base_color, num_shades):
    rgba_array = np.linspace(0.2, 1, num_shades)  # Variations de l'intensité, 0.2 recommandé pour le bleu, 0.4 pour le reste
    return [(*base_color[:3], alpha) for alpha in rgba_array]


## Plots the final electricity grid consumption
def plot_final_grid_cons(year, transformer, plot_capacity=False, capacity_lim=False, pvhp=True):
    t = np.arange(1,25,1)
    df = pd.read_pickle(f'../examples/results/{transformer}/fix/7a_{transformer}_{year}_fix.pickle')
    df_relax = pd.read_pickle(f'../examples/results/{transformer}/fix/7a_{transformer}_{year}_fix_relax.pickle')

    # if not pvhp:
    #     df = pd.read_pickle(f'../examples/results/{transformer}/{year}/noPVHP/7a_{transformer}_{year}_no_PVHP.pickle')
    # else:
    #     df = pd.read_pickle(f'../examples/results/{transformer}/{year}/7a_{transformer}_{year}.pickle')

    df_building_t = df['totex'][0]['df_Buildings_t']
    working_df = df['totex'][0]['df_Unit_t'].xs('Electricity', level='Layer')
    working_df_grid = df['totex'][0]['df_Grid_t'].xs('Electricity', level='Layer')

    # mobility electricity consumption
    E_trolley = dict()
    E_ebus = dict()
    E_metro = dict()
    E_EV_charger = dict()

    # buildings electricity consumption
    E_HP_a = dict()
    E_HP_geo = dict()
    E_dom_elec = dict()

    # PV 
    E_PV = dict()
    E_PV_export = dict()
    E_EV_supply = dict()

    for p in range(1,11):
        E_trolley[p] = 24*[0]
        E_ebus[p] = 24*[0]
        E_metro[p] = 24*[0]
        E_EV_charger[p] = 24*[0]
        E_HP_a[p] = 24*[0]
        E_HP_geo[p] = 24*[0]
        E_dom_elec[p] = 24*[0]
        E_PV[p] = 24*[0]
        E_PV_export[p] = 24*[0]
        E_EV_supply[p] = 24*[0]

    # iteration for housing
    for i in range(len(df_building_t.index.get_level_values('Hub').unique())):
        for p in range(1,11):
            E_HP_a[p] += round(working_df.xs(f'HeatPump_Air_Building{i+1}', level='Unit').xs(p, level='Period')['Units_demand'],3)
            E_HP_geo[p] += round(working_df.xs(f'HeatPump_Geothermal_Building{i+1}', level='Unit').xs(p, level='Period')['Units_demand'],3)
            E_dom_elec[p] += round(df_building_t.xs(f'Building{i+1}', level='Hub').xs(p, level='Period')['Domestic_electricity'],3)
            E_PV[p] += round(working_df.xs(f'PV_Building{i+1}', level='Unit').xs(p, level='Period')['Units_supply'],3)

    # iteration over mobility only
    for p in range(1,11):
        E_trolley[p] = working_df.xs('TrolleyBus_district', level='Unit').xs(p, level='Period')['trolley_demand']
        E_ebus[p] = working_df.xs('ElectricBus_district', level='Unit').xs(p, level='Period')['ebus_demand']
        E_metro[p] = working_df.xs('Metro_district', level='Unit').xs(p, level='Period')['metro_demand']
        E_EV_charger[p] = working_df.xs('EV_charger_district', level='Unit').xs(p, level='Period')['Units_demand']
        E_PV_export[p] = round(working_df_grid.xs('Network', level='Hub').xs(p, level='Period')['Grid_demand'],3)
        E_EV_supply[p] = working_df.xs('EV_charger_district', level='Unit').xs(p, level='Period')['Units_supply']

    E_trolley_r, E_ebus_r, E_metro_r, E_HP_a_r, E_HP_geo_r, E_EV_charger_r, E_dom_elec_r, E_PV_r, E_PV_export_r, E_EV_supply_r = generate_final_grid_cons(year, transformer, relax=True)

            
    for p in range(1,11):
        total_cons = E_trolley[p] + E_ebus[p] + E_metro[p] + E_HP_a[p] + E_HP_geo[p] + E_EV_charger[p] + E_dom_elec[p]
        pv_supply = E_PV[p]-E_PV_export[p]+E_EV_supply[p]
        grid_cons = np.array(total_cons - pv_supply)

        total_cons_r = E_trolley_r[p] + E_ebus_r[p] + E_metro_r[p] + E_HP_a_r[p] + E_HP_geo_r[p] + E_EV_charger_r[p] + E_dom_elec_r[p]
        pv_supply_r = E_PV_r[p]-E_PV_export_r[p]+E_EV_supply_r[p]
        grid_cons_r = np.array(total_cons_r - pv_supply_r)

        plt.figure(figsize=(8, 5))
        plt.plot(t, grid_cons, color='deepskyblue', label=r'$\tau = 0.03$')
        plt.plot(t, grid_cons_r, color='coral', label=r'$\tau = 0.3$')

        if plot_capacity:
            capacity = 3*transformer_capacity(transformer,np.nan)
            plt.axhline(capacity, color='purple', linestyle='dotted', label='Transformer maximum capacity')

        plt.title(f'{transformer} - {year} - Period {p}')
        plt.xlabel('t (hours)')
        plt.ylabel('Final grid consumption (kW)')
        plt.legend()
        plt.grid()

        plt.tight_layout()

        # if plot_capacity:
        #     plt.savefig(f'figure/{transformer}/{year}/elec/final_grid_cons/final_grid_cons_cap_{p}.png')
        # else:
        #     plt.savefig(f'figure/{transformer}/{year}/elec/final_grid_cons/final_grid_cons_cap_{p}.png')
        #plt.savefig(f'figure/{transformer}/{year}/relaxation/final_grid_cons/no_title/final_grid_cons_comp_{p}_{year}.png')
        plt.savefig(f'figure/{transformer}/fix/relax/final_grid_cons/final_grid_cons_comp_{p}_{year}.png')

        plt.show()


## Generate all the variables to plot the final grid consumption, called by the previous function to compare two different relaxation
def generate_final_grid_cons(year, transformer, pvhp=True, relax=False):
    if not pvhp:
        df = pd.read_pickle(f'../examples/results/{transformer}/{year}/noPVHP/7a_{transformer}_{year}_no_PVHP.pickle')
    else:
        df = pd.read_pickle(f'../examples/results/{transformer}/{year}/7a_{transformer}_{year}.pickle')

    if relax:
        df = pd.read_pickle(f'../examples/results/{transformer}/fix/7a_{transformer}_{year}_fix_relax.pickle')


    df_building_t = df['totex'][0]['df_Buildings_t']
    working_df = df['totex'][0]['df_Unit_t'].xs('Electricity', level='Layer')
    working_df_grid = df['totex'][0]['df_Grid_t'].xs('Electricity', level='Layer')

    # mobility electricity consumption
    E_trolley = dict()
    E_ebus = dict()
    E_metro = dict()
    E_EV_charger = dict()

    # buildings electricity consumption
    E_HP_a = dict()
    E_HP_geo = dict()
    E_dom_elec = dict()

    # PV 
    E_PV = dict()
    E_PV_export = dict()
    E_EV_supply = dict()

    for p in range(1,11):
        E_trolley[p] = 24*[0]
        E_ebus[p] = 24*[0]
        E_metro[p] = 24*[0]
        E_EV_charger[p] = 24*[0]
        E_HP_a[p] = 24*[0]
        E_HP_geo[p] = 24*[0]
        E_dom_elec[p] = 24*[0]
        E_PV[p] = 24*[0]
        E_PV_export[p] = 24*[0]
        E_EV_supply[p] = 24*[0]

    # iteration for housing
    for i in range(len(df_building_t.index.get_level_values('Hub').unique())):
        for p in range(1,11):
            E_HP_a[p] += round(working_df.xs(f'HeatPump_Air_Building{i+1}', level='Unit').xs(p, level='Period')['Units_demand'],3)
            E_HP_geo[p] += round(working_df.xs(f'HeatPump_Geothermal_Building{i+1}', level='Unit').xs(p, level='Period')['Units_demand'],3)
            E_dom_elec[p] += round(df_building_t.xs(f'Building{i+1}', level='Hub').xs(p, level='Period')['Domestic_electricity'],3)
            E_PV[p] += round(working_df.xs(f'PV_Building{i+1}', level='Unit').xs(p, level='Period')['Units_supply'],3)

    # iteration over mobility only
    for p in range(1,11):
        E_trolley[p] = working_df.xs('TrolleyBus_district', level='Unit').xs(p, level='Period')['trolley_demand']
        E_ebus[p] = working_df.xs('ElectricBus_district', level='Unit').xs(p, level='Period')['ebus_demand']
        E_metro[p] = working_df.xs('Metro_district', level='Unit').xs(p, level='Period')['metro_demand']
        E_EV_charger[p] = working_df.xs('EV_charger_district', level='Unit').xs(p, level='Period')['Units_demand']
        E_PV_export[p] = round(working_df_grid.xs('Network', level='Hub').xs(p, level='Period')['Grid_demand'],3)
        E_EV_supply[p] = working_df.xs('EV_charger_district', level='Unit').xs(p, level='Period')['Units_supply']


    return E_trolley, E_ebus, E_metro, E_HP_a, E_HP_geo, E_EV_charger, E_dom_elec, E_PV, E_PV_export, E_EV_supply

        
## Plots the EV-stored electricity        
def plot_SOC(year, transformer, plot_capacity=False, pvhp=True):
    t = np.arange(1,25,1)
    #df_relax = pd.read_pickle(f'../examples/results/7a_{transformer}_{year}_relax_0.3_battery.pickle')
    df_relax = pd.read_pickle(f'../examples/results/{transformer}/fix/7a_{transformer}_{year}_fix_relax.pickle')
    df = pd.read_pickle(f'../examples/results/{transformer}/fix/7a_{transformer}_{year}_fix.pickle')

    working_df = df['totex'][0]['df_Unit_t'].xs('Electricity', level='Layer')
    working_df_relax = df_relax['totex'][0]['df_Unit_t'].xs('Electricity', level='Layer')

    EV_fleet = df['totex'][0]['df_Unit']['Units_Mult'].loc['EV_district']
    EV_fleet_relax = df_relax['totex'][0]['df_Unit']['Units_Mult'].loc['EV_district']

    SOC = dict()
    SOC_relax = dict()

    for p in range(1,11):
        SOC[p] = 24*[0]
        SOC_relax[p] = 24*[0]

    for p in range(1,11):
        SOC[p] = working_df.xs('EV_district', level='Unit').xs(p, level='Period')['EV_E_stored']    #/(EV_fleet * 70)*100
        SOC_relax[p] = working_df_relax.xs('EV_district', level='Unit').xs(p, level='Period')['EV_E_stored']    #/(EV_fleet_relax * 70)*100

        plt.figure(figsize=(8, 5))
        plt.plot(t, SOC[p], label=r'$\tau = 0.03$')
        plt.plot(t, SOC_relax[p], label=r'$\tau = 0.3$')

        if plot_capacity:
            capacity = 3*transformer_capacity(transformer,np.nan)
            plt.axhline(capacity, color='purple', linestyle='dotted', label='Transformer maximum capacity')

        if transformer == 3230:
            if year == 2024:
                plt.ylim([16000,24000])
            elif year == 2030:
                plt.ylim([37000,47000])
            else:
                plt.ylim([62000,74000])
        elif transformer == 3195:
            if year == 2024:
                plt.ylim([5100,8000])
            elif year == 2030:
                plt.ylim([14000,19000])
            else:
                plt.ylim([23000,28000])
        elif transformer == 3216:
            if year == 2024:
                plt.ylim([900,1400])
            elif year == 2030:
                plt.ylim([2700,3300])
            else:
                plt.ylim([4300,5100])
        elif transformer == 3217:
            if year == 2024:
                plt.ylim([21000,32000])
            elif year == 2030:
                plt.ylim([49000,60000])
            else:
                plt.ylim([80000,92000])

        plt.title(f'{transformer} - {year} - Period {p}')
        plt.xlabel('t (hours)')
        plt.ylabel('Electricity stored in EV batteries (kWh)')
        plt.legend()
        plt.grid()
        plt.savefig(f'figure/{transformer}/fix/relax/SOC/SOC_comp_{p}_{year}.png')

        plt.tight_layout()
        plt.show()      
    

def generate_population():
    result = pd.read_pickle("data/mixture_LAU_9.pickle")
    id = result["Best iter id"]
    cluster_list = result['typical districts id'].iloc[id]
    population = dict()
    for xx in [2024, 2030, 2050]:
        population[xx] = dict()

    pers_m2 = 40                                                                    # cf normes 2024-2015
    for x in cluster_list:
        population[2024][f'{x}'] = result['Data']['ERA'].loc[x]/pers_m2
        population[2030][f'{x}'] = (result['Data']['ERA'].loc[x]/pers_m2) * 1.1
        population[2050][f'{x}'] = (result['Data']['ERA'].loc[x]/pers_m2) * 1.28
    
    return population


def percentage_evol():
    gdf = gpd.read_file('data/transfo_lausanne_connectivity.gpkg')
    result = pd.read_pickle("data/mixture_LAU_9.pickle")
    id = result["Best iter id"]
    cluster_list = result['typical districts id'].iloc[id]
    cluster_list.loc[len(cluster_list)] = 3216

    connec_value = gdf['connectivity level']
    connec_typical_value = dict()
    for x in cluster_list:
        connec_typical_value[f'{x}'] = result['Data'][result['Data']['id']==x]['connectivity level']
        connec_typical_value[f'{x}'] = connec_typical_value[f'{x}'].values[0]
    #connec_typical_value.sort_values(by='')

    stat_data = [np.mean(connec_value),np.median(connec_value)]

    percentages = dict()
    for xx in [2024, 2030, 2050]:
        percentages[xx] = dict()

    base_2024 = {'Voiture': 72.9, 'TP': 20.8, 'MD': 6.3}                             # d'après OFS
    base_2030 = {'Voiture': 72.3, 'TP': 21.1, 'MD': 6.6}
    base_2050 = {'Voiture': 67.6, 'TP': 24.3, 'MD': 8.1}
    bases = {2024 : base_2024,
             2030 : base_2030,
             2050 : base_2050}
    

    for xx in [2024, 2030, 2050]:
        for cluster in cluster_list:
            new_perc = [0]*3
            new_perc[1] = round(bases[xx]['TP'] * (1 + (connec_typical_value[f'{cluster}'] - stat_data[0])/stat_data[0]) / 100,3)
            new_perc[2] = round(bases[xx]['MD'] * (1 + (connec_typical_value[f'{cluster}'] - stat_data[0])/stat_data[0]) / 100,3)
            new_perc[0] = 1 - new_perc[1] - new_perc[2]
            percentages[xx][cluster] = new_perc

            if new_perc[0] + new_perc[1] + new_perc[2] != 1:
                print("erreur dans les pourcentages in : ", cluster, xx)
                return 

    return percentages


def write_modalshares():
    percentages = percentage_evol()

    for year, data in percentages.items():
        for cluster, perc in data.items():
            filename = f"modalshares_{year}_{cluster}.csv"
            csv_dir1 = f"../../reho/data/mobility/modalshares.csv"
            csv_dir2 = f"../../reho/data/mobility/modalshares/{year}/"
            with open(f"{csv_dir1}", "r") as file:
                lines = file.readlines()
            with open(f"{csv_dir2}{filename}", "w") as file:
                file.writelines(lines[:-3])
                file.writelines([f'cars,0,{perc[0]},0,{perc[0]}\n',
                                 f'PT,0,{perc[1]},0,{perc[1]}\n',
                                 f'MD,0,{perc[2]},0,{perc[2]}'])


def write_population():
    population = generate_population()
    csv_dir = "../../reho/data/mobility/population.csv"

    # Rassembler les données pour correspondre aux lignes
    rows = []
    keys = set(key for subdict in population.values() for key in subdict)  # Union de toutes les clés des sous-dictionnaires
    for key in keys:
        row = {col: round(population[col].get(key, ''),0) for col in population}
        row["cluster"] = key  # Ajouter l'index pour conserver les clés des sous-dictionnaires
        rows.append(row)

    # Déterminer les noms des colonnes
    columns = ["cluster"] + list(population.keys())

    # Écriture dans le fichier CSV
    with open(csv_dir, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    # with open(csv_dir, "w", newline="") as csvfile:
    #     writer = csv.writer(csvfile)
    #     writer.writerow(['cluster', 'population'])
    #     for cluster, pop in population.items():
    #         writer.writerow([cluster, pop])


def plot_EV_charging_profile():
    t = np.arange(1,25,1)
    file = pd.read_csv("../../reho/data/mobility/dailyprofiles.csv")

    day = file.loc[:,file.columns.str.contains("EV_cpfwdy")]
    we = file.loc[:,file.columns.str.contains("EV_cpfwnd")]         # spoiler alert they are identical

    day_high = day * 1.03
    day_low = day * 0.97


    fig1, ax1 = plt.subplots(figsize=(8, 5))
    fig2, ax2 = plt.subplots(figsize=(8, 5))

    ax1.plot(t, day)
    ax1.plot(t, day_high, color='deepskyblue')
    ax1.plot(t, day_low, color='deepskyblue')
    ax1.fill_between(t, day_low['EV_cpfwdy'], day_high['EV_cpfwdy'], color='deepskyblue', alpha=0.3)
    ax1.set_xlabel("hours")
    ax1.set_ylabel("Electric consumption (kW)")
    # ax1.yaxis.set_ticks([])  
    # ax1.yaxis.set_ticklabels([])
    ax1.set_title("Weekday")
    ax1.grid(True)

    # ax2.plot(t, we)
    # ax2.set_xlabel("hours")
    # ax2.set_ylabel("Electric consumption (kW)")
    # # ax2.yaxis.set_ticks([])  
    # # ax2.yaxis.set_ticklabels([])
    # ax2.set_title("Weekend")
    # ax2.grid(True)

    fig1.tight_layout()
    fig1.savefig("figure/weekday_EV_charging_margin3")
    #fig2.tight_layout()
    #fig2.savefig("figure/weekend_EV_charging_yaxis")

    plt.show()


if __name__ == '__main__':
    #generate_bus_charging_profile()
    #connectivity_plot()
    #plot_grid_supply(2024, 3195, 1)
    #plot_grid_supply(2024, 10680, 2)

    cluster_list = [3195, 3217, 3230, 10481, 10491]
    # for x in cluster_list:
    #     plot_grid_supply_mob(2024, x, 1)
    #     plot_grid_supply_mob(2024, x, 2)

    # population = generate_population()
    # print(population)

    # perc = percentage_evol()
    # print(perc)
    #write_modalshares()
    #write_population()
    #capacity = 3*transformer_capacity(3230,np.nan)
    #pickle_cap = pd.read_pickle(f"shared_folder/1a_3157.pickle")
    #capacity = 3*transformer_capacity(np.nan,pickle_cap)
    #print(capacity)
    for x in [3230]:
        for y in [2050]:
            #plot_grid_supply_total(y,x,plot_capacity=True,pvhp=True)
            #plot_grid_supply_mob(y,x,plot_capacity=True,pvhp=True)
            #plot_elec_ext(y,x,plot_capacity=True,pvhp=True)
            #plot_final_grid_cons(y,x,plot_capacity=True)
            plot_SOC(y,x)
    #plot_elec_ext(2024, 3217, plot_capacity=True, capacity_lim=True)
    #plot_grid_supply_total(2024, 3217, plot_capacity=True, capacity_lim=True)
    #plot_grid_supply_mob(2024, 3217, plot_capacity=False)

    # base_color_mob = to_rgba('navy', alpha=0.6)
    # shades = generate_shades(base_color_mob, 4)
    # shades_hex = []
    # for x in shades:
    #     shades_hex.append(to_hex(x, keep_alpha=False))
    # print(shades_hex)

    #plot_EV_charging_profile()
    
    
