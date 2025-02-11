######################################################################################################################################
#### Extrapolation file to the entire city. Each typical district is extrapolated to the rest of its class according to their ERA ####
#### All non-typical district's maximum capacity has been computed according to the baseline files located in shared_folder       ####
#### Two functions, computed the total and PV produced electricity, are used by assign_color_to_gpkg() to give each district      ####
#### its color and then plot it via the plot_map() function. Some other functions necessary to the process are detailed below.    ####
######################################################################################################################################


import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.colors import Normalize, to_rgba
from matplotlib.colorbar import ColorbarBase
import matplotlib.cm as cm
import os
import contextily as cx
from tqdm import tqdm
from fonction import transformer_capacity
from matplotlib.patches import Patch
import matplotlib.gridspec as gridspec



excel = pd.read_excel("data/mixture_LAU_9_bd.xlsx")
gpkg = gpd.read_file("data/transfo_lausanne_connectivity.gpkg")
excel_filt = excel[(excel['cluster']=='Cluster 4') | (excel['cluster']=='Cluster 5') | (excel['cluster']=='Cluster 6') | (excel['cluster']=='Cluster 9')]

typical_cluster_dict = {3195 : 'Cluster 4',
                          3216 : 'Cluster 5',
                          3217 : 'Cluster 9',
                          3230 : 'Cluster 6'}

typical_ERA_dict = {3195 : excel[excel['id']==3195]['ERA'][32],
                    3216 : excel[excel['id']==3216]['ERA'][44],
                    3217 : excel[excel['id']==3217]['ERA'][45],
                    3230 : excel[excel['id']==3230]['ERA'][58]}


## Compute the total electricity consumption of a given district and year 
def total_consumption(year, transformer):
    #df = pd.read_pickle(f'../examples/results/{transformer}/{year}/7a_{transformer}_{year}_relax_0.3.pickle')
    df = pd.read_pickle(f'../examples/results/{transformer}/fix/7a_{transformer}_{year}_fix_relax.pickle')

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
    data = dict()

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
        data[p] = 24*[0]

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
            

    for p in range(1,11):
        E_mob_rest = [tro+bus+met for tro,bus,met in zip(E_trolley[p],E_ebus[p],E_metro[p])]
        E_EH = [dhw+sh for dhw,sh in zip(E_EH_dhw[p],E_EH_sh[p])]
        E_HP = [a+geo for a,geo in zip(E_HP_a[p],E_HP_geo[p])]

        E_mob = np.array([E_mob_rest, E_EV_charger[p]])
        E_housing = np.array([E_AC[p], E_HP, E_dom_elec[p]])
        data_to_plot = np.array([E_mob_rest, E_EV_charger[p], E_AC[p], E_HP, E_dom_elec[p]])
        data[p] = np.sum(data_to_plot, axis=0)
    
    return data

## Compute the outside-the-grid produced electricity of a given district and year 
def PV_consumption(year, transformer):
    #df = pd.read_pickle(f'../examples/results/{transformer}/{year}/7a_{transformer}_{year}_relax_0.3.pickle')
    df = pd.read_pickle(f'../examples/results/{transformer}/fix/7a_{transformer}_{year}_fix_relax.pickle')

    df_building_t = df['totex'][0]['df_Buildings_t']
    working_df = df['totex'][0]['df_Unit_t'].xs('Electricity', level='Layer')
    working_df_grid = df['totex'][0]['df_Grid_t'].xs('Electricity', level='Layer')

    E_PV = dict()
    E_PV_export = dict()
    E_battery = dict()
    E_EV = dict()
    data = dict()

    for p in range(1,11):
        E_PV[p] = 24*[0]
        E_PV_export[p] = 24*[0]
        E_battery[p] = 24*[0]
        E_EV[p] = 24*[0]
        data[p] = 24*[0]
        

    for p in range(1,11):
        E_EV[p] = working_df.xs('EV_charger_district', level='Unit').xs(p, level='Period')['Units_supply']
        E_PV_export[p] = round(working_df_grid.xs('Network', level='Hub').xs(p, level='Period')['Grid_demand'],3)
        for i in range(len(df_building_t.index.get_level_values('Hub').unique())):
            E_PV[p] += round(working_df.xs(f'PV_Building{i+1}', level='Unit').xs(p, level='Period')['Units_supply'],3)
            E_battery[p] += round(working_df.xs(f'Battery_Building{i+1}', level='Unit').xs(p, level='Period')['Units_demand'],3)


    for p in range(1,11):
        data_to_plot = np.array([E_PV[p]-E_PV_export[p], E_PV_export[p],  E_EV[p], E_battery[p]])
        data[p] = np.array(E_PV[p]-E_PV_export[p]+E_EV[p])

    return data


## Compute the size of each typical period as a preparation of the future annualisation step
def compute_index():
    df = pd.read_pickle(f'../examples/results/3230/2024/7a_3230_2024.pickle')       # no matter the year and the transformer since the temporal clustering stays the same
    tab = df['totex'][0]['df_Index']
    index = dict()
    for p in range(1,11):
        index[p] = len(tab[tab['PeriodOfYear']==p])/24
    
    return index
# try np.sum(np.array([index[p] for p in range(1,11)])) to check that the sum is indeed 365
    

## According to the given consumption and production files, as well as the right capacity, this function computes the district's color scores 
def set_color(total,pv,capacity):
    grid = dict()
    index = compute_index()
    for p in range(1,11):
        grid[p] = total[p] - pv[p]

    green_list = []
    orange_list = []
    red_list = []

    for p in range(1,11):
        green = 0
        orange = 0
        red = 0
        for h in range(len(grid[p])):
            if grid[p][h] >= 1.1 * capacity:
                red += 1
            elif grid[p][h] >= 0.9 * capacity:
                orange += 1
            else:
                green += 1
        red_list.append(red * index[p])
        orange_list.append(orange * index[p])
        green_list.append(green * index[p])
    
    colors = [np.sum(red_list), np.sum(orange_list), np.sum(green_list)]
    
    return colors

def rechercher_fichier(folder, file):
    # Parcourt tous les fichiers dans le dossier
    for racine, _, fichiers in os.walk(folder):
        if file in fichiers:
            return True
    return False


## Combine the color scores to the geopackage file
def add_color_to_gpkg(geo,xls,year):
    green = 93 * [0]                # the length of the total excel file, we will drop the non-desired ones later
    orange = 93 * [0]
    red = 93 * [0]

    for id in tqdm(excel_filt['id'], total=len(excel_filt)):
        filename = f"1a_{id}.pickle"
        line = excel[excel['id']==id].index[0]
        if id in typical_cluster_dict.keys():
            transfo_cap = 3 * transformer_capacity(id,np.nan)

            id_cons_dict = total_consumption(year,id)
            id_pv_dict = PV_consumption(year,id)
        elif not rechercher_fichier("shared_folder",filename):
            #print(excel[excel['id']==id].index)
            continue
        else:
            pickle_cap = pd.read_pickle(f"shared_folder/1a_{id}.pickle")
            transfo_cap = 3 * transformer_capacity(np.nan,pickle_cap)

            era = excel[excel['id']==id]['ERA'][line]
            cluster = excel[excel['id']==id]['cluster'][line]
            typical_cluster = next((k for k, v in typical_cluster_dict.items() if v == cluster), None)

            factor = (era / typical_ERA_dict[typical_cluster])
            total_dict = total_consumption(year,typical_cluster)
            pv_dict = PV_consumption(year,typical_cluster)
            id_cons_dict = {key: np.array([x * factor for x in values]) for key, values in total_dict.items()}
            id_pv_dict = {key: np.array([x * factor for x in values]) for key, values in pv_dict.items()}

        colors = set_color(id_cons_dict,id_pv_dict,transfo_cap)
        red[line] = colors[0]
        orange[line] = colors[1]
        green[line] = colors[2]

    xls['red'] = red
    xls['orange'] = orange
    xls['green'] = green

    xls_filt = xls[(xls['cluster']=='Cluster 4') | (xls['cluster']=='Cluster 5') | (xls['cluster']=='Cluster 6') | (xls['cluster']=='Cluster 9')]
    #xls_filt2 = xls_filt[(xls_filt['id']!=3179) | (xls_filt['id']!=3182) | (xls_filt['id']!=10677) | (xls_filt['id']!=10680)]
    xls_filt = xls_filt.drop(columns=['geometry','rho_household','rho_industry','rho_service','connectivity level'])

    geo_merged = geo.merge(xls_filt, on='id', how='left')
    geo_merged = geo_merged.dropna(subset='cluster')
    geo_merged.to_file(f"data/transfo_lausanne_color_{year}_fix_relax.gpkg", layer='transfo', driver="GPKG")


def assign_color(row, norm_red, norm_orange, norm_green):
    if row['red'] > 0:  
        return row['red']
    elif row['orange'] > 0:  
        return row['orange']
    else:  
        return row['green']

## Not used
def plot_map_zero(geo):
    red_values = geo['red']
    orange_values = geo['orange']
    green_values = geo['green']
    
    norm_red = Normalize(vmin=red_values.min(), vmax=red_values.max())
    norm_orange = Normalize(vmin=orange_values.min(), vmax=orange_values.max())
    norm_green = Normalize(vmin=green_values.min(), vmax=green_values.max())

    color = geo.apply(assign_color, axis=1, norm_red=norm_red, norm_orange=norm_orange, norm_green=norm_green)
    
    fig = plt.figure(figsize=(12, 6))
    gs = gridspec.GridSpec(1, 4, width_ratios=[10, 0.4, 0.4, 0.4])
    ax = fig.add_subplot(gs[0])

    # geo = geo.to_crs(epsg=3857)
    #cx.add_basemap(ax, crs=geo.crs.to_string())
    # cx.add_basemap(ax, crs="EPSG:3857", source=cx.providers.OpenStreetMap.Mapnik)
    # xmin, ymin, xmax, ymax = geo.total_bounds

    geo.plot(
        ax=ax,
        color=color,
        edgecolor="black" 
    )
    # Colorbar for red
    sm_rouge = cm.ScalarMappable(cmap="Reds", norm=norm_red)
    sm_rouge._A = []  
    cbar_rouge_ax = fig.add_subplot(gs[1])
    cbar_rouge = fig.colorbar(sm_rouge, cax=cbar_rouge_ax, orientation="vertical")
    cbar_rouge.set_label("High risk of overreaching")

    # Colorbar pour la couleur orange
    sm_orange = cm.ScalarMappable(cmap="Oranges", norm=norm_orange)
    sm_orange._A = []  
    cbar_orange_ax = fig.add_subplot(gs[2])
    cbar_orange = fig.colorbar(sm_orange, cax=cbar_orange_ax, orientation="vertical")
    cbar_orange.set_label("Medium risk of overreaching")

    # Colorbar pour la couleur verte
    sm_vert = cm.ScalarMappable(cmap="Greens", norm=norm_green)
    sm_vert._A = []  
    cbar_vert_ax = fig.add_subplot(gs[3])
    cbar_vert = fig.colorbar(sm_vert, cax=cbar_vert_ax, orientation="vertical")
    cbar_vert.set_label("Low risk of overreaching")

    # legend_labels = [
    # Patch(color="red", alpha=0.7),
    # Patch(color="orange", alpha=0.7),
    # Patch(color="green", alpha=0.7),
    # ]

    #ax.legend(handles=legend_labels, title="Color legend", loc="upper right", fontsize=12)
    #ax.set_title("Carte des districts avec intensité modulée par valeur", fontsize=16)
    # ax.set_xlim(xmin, xmax)
    # ax.set_ylim(ymin, ymax)
    ax.axis("off")  
    #plt.subplots_adjust(left=0.05, right=0.85, top=0.9, bottom=0.1)  
    plt.tight_layout() 
    plt.show()


## Plot the color map from the geopackage file
def plot_map(geo, year):
    #geo = geo[~geo.index.isin([23,25,75,77])]              # uncomment if you want to filter the map and cancel the four red permanent districts
    red_norm = geo['red']/8760
    orange_norm = geo['orange']/8760
    green_norm = geo['green']/8760

    #combined_color = (red_norm * 1 + orange_norm * 0.1 + green_norm * 0.01)
    combined_color = [0] * len(geo)
    for i in range(len(geo)):
        # if i in [23,25,75,77]:                            # uncomment these lines too if you plan to filter the map
        #     combined_color[i] = None                      # don't forget to transform the following 'if' in 'elif' if so
        if geo['red'][i] > 0:  # elif ssi on veut filtrer
            combined_color[i] = (2/3) + red_norm[i]/3
        elif geo['orange'][i] > 0:
            combined_color[i] = (1/3) + orange_norm[i]/3
        elif geo['green'][i] > 0:
            combined_color[i] = 1/3 - green_norm[i]/3
        else:
            combined_color[i] = None
        
    cmap = cm.get_cmap("RdYlGn_r", 256)  
    filtered_data = [x for x in combined_color if x is not None]
    norm = Normalize(vmin=0, vmax=max(filtered_data))

    #color = combined_color.apply(lambda x: colors.to_hex(cmap(norm(x))))
    color = ['#FFFFFF' if x is None else colors.to_hex(cmap(norm(x))) for x in combined_color]
    
    fig = plt.figure(figsize=(12, 6))
    gs = gridspec.GridSpec(1, 2, width_ratios=[10, 1])
    ax = fig.add_subplot(gs[0])

    # geo = geo.to_crs(epsg=3857)
    #cx.add_basemap(ax, crs=geo.crs.to_string())
    # cx.add_basemap(ax, crs="EPSG:3857", source=cx.providers.OpenStreetMap.Mapnik)
    # xmin, ymin, xmax, ymax = geo.total_bounds

    geo.plot(
        ax=ax,
        color=color,
        edgecolor="black" 
    )

    # Colorbar 
    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm._A = []  
    cbar = fig.colorbar(sm, ax=ax, orientation="vertical")
    cbar.set_label("Risk of overreaching the transformer capacity")
    cbar.ax.hlines(2/3, xmin=0, xmax=1, color="black", linewidth=1)
    #cbar.ax.text(0.5, 2/3, "", va='center', ha='left', color="black", fontsize=8)
    cbar.ax.hlines(1/3, xmin=0, xmax=1, color="black", linewidth=1)



    # legend_labels = [
    # Patch(color="red", alpha=0.7),
    # Patch(color="orange", alpha=0.7),
    # Patch(color="green", alpha=0.7),
    # ]

    #ax.legend(handles=legend_labels, title="Color legend", loc="upper right", fontsize=12)
    #ax.set_title("Carte des districts avec intensité modulée par valeur", fontsize=16)
    # ax.set_xlim(xmin, xmax)
    # ax.set_ylim(ymin, ymax)
    ax.axis("off")  
    plt.subplots_adjust(left=0.05, right=0.85, top=0.9, bottom=0.1) 
    plt.savefig(f"figure/risk_map_{year}_fix_relax.png") 
    plt.tight_layout() 
    plt.show()

    

if __name__ == '__main__':
    #add_color_to_gpkg(gpkg, excel, 2050)
    gpkg_color = gpd.read_file("data/transfo_lausanne_color_2030_fix.gpkg")
    plot_map(gpkg_color, 2030)
        

    



     

# data = total_consumption(2030, 3230)
# pv_cons = PV_consumption(2030, 3230)
# print(data)
