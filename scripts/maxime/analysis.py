######################################################################################################################################
#### This file plots all the relevant clustering maps: whole city, all typical districts and each of them ind. with building data ####
######################################################################################################################################


import matplotlib as mpl
import matplotlib.pyplot as plt
import geopandas as gpd
import rasterio.plot
from reho.model.reho import *
import contextily as cx
from matplotlib_scalebar.scalebar import ScaleBar
from matplotlib.colors import LinearSegmentedColormap
from shapely.wkt import loads

#colors_dark = ['#00A79F', '#007480', '#cdc50a','#84b701','#8B2323', '#FF0000'] 
colors_dark = ['#00A79F', '#007480', '#FF7F50','#84b701','#8B2323', '#FF0000' ] # modification to give more contrast between cluster 5 and 6
EPFL_dark = LinearSegmentedColormap.from_list("custom", colors_dark, N=256)

def plot_map_CH(swiss_districts, path, CH_map=None, show_n=False):
    # Convert swiss_districts to a GeoDataFrame if it is not already one
    if not isinstance(swiss_districts, gpd.GeoDataFrame):
        swiss_districts = gpd.GeoDataFrame(swiss_districts, geometry='geometry')

    with rasterio.open(path+'/relief.tif') as src:
        img_extent = [src.bounds[0], src.bounds[2], src.bounds[1], src.bounds[3]]

    swiss_districts['cluster'] = swiss_districts['cluster'].astype(str)
    swiss_districts.fillna(0, inplace=True)
    swiss_districts.replace([np.inf, -np.inf], 0, inplace=True)

    fig, ax = plt.subplots(figsize=(9, 7))
    bounds = pd.DataFrame([swiss_districts.geometry.loc[i].bounds for i in swiss_districts.geometry.index])
    plt.xlim(bounds[0].min() * 0.9995, bounds[2].max() * 1.0015)
    plt.ylim(bounds[1].min() * 0.998, bounds[3].max() * 1.001)
    ax.imshow(CH_map, cmap='gray', extent=img_extent)  # Plot the raster data
    swiss_districts.plot(column='cluster', ax=ax, legend=True, alpha=0.7, cmap=EPFL_dark.reversed(), legend_kwds={'fontsize': 12, "frameon": True, "loc": 'upper right'})
    ax.axis('off')
    scalebar = ScaleBar(1, location='lower right')  # Assuming your data is in meters
    ax.add_artist(scalebar)
    if show_n:
        sorted_districts = swiss_districts.sort_values(by='cluster')
        coordinates = swiss_districts.get_coordinates().groupby(level="transformer").min()
        for i, keys in enumerate(sorted_districts.index):
            ax.text(coordinates.loc[keys][0]+300, coordinates.loc[keys][1]+300, str(i+1), color="red", fontsize=20)             # ne pas oublier le i+1 quand on run avec la connectivité
    plt.show()
    if show_n:
        fig.savefig('figure/'+'map_clusters_typical'+'_LAU_'+str(n)+'_n.pdf')
    else:
        fig.savefig('figure/'+'map_clusters'+'_LAU_'+str(n)+'_n.pdf')
    return

def add_basemap_with_retry(ax, crs, retries=3, delay=5):
    for attempt in range(retries):
        try:
            cx.add_basemap(ax, crs=crs)
            return
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise


n = 9
try:
    os.mkdir("figure/"+"LAU_" + str(n))
except:
    pass

path = "../../../qbuildings/GBuildings/data_analysis/typical_district"
#results = pd.read_excel(path+"/output/kmedoids_LAU_9_n.xlsx", index_col=0, sheet_name=None)
results = pd.read_excel(path+"/output/mixture_LAU_9_bd.xlsx", index_col=0, sheet_name=None)
results['raw_data']["geometry"] = results['raw_data']["geometry"].apply(lambda geom: loads(geom) if isinstance(geom, str) else geom)

best_id = results['results']['best_iter_id'][0]
#clustering = results["typical_district_id"][best_id]
#results["raw_data"]["cluster"] = clustering.labels_  # get the typical district label for each district

typical_districts = results['typical_district_id'].iloc[best_id]  # get the list of typical districts
#typical_districts.drop('iter', axis=1, inplace=True)              # delete the column 'iter'
typical_districts.iloc[5] = 3216            # substitute 10491 by 3196 because better clzss representant
typical_districts = typical_districts.transpose()
typical_districts_data = results["raw_data"].loc[typical_districts]

# code pour ordoner les districts selon connectivité croissante si ça n'a pas été fait dans run_cluster_connectivity.py
# cluster_class = pd.read_pickle(path+"/scripts/results/kmedoids_LAU_9_n.pickle")
# cluster_list = cluster_class['typical districts id'].iloc[best_id]
# dict_connec = {x: cluster_class['Data']['connectivity level'][x] for x in cluster_list}
# sorted_dict = dict(sorted(dict_connec.items(), key=lambda x: x[1]))
# sorted_dict_cluster = {}
# cluster_class['Data']["label"] = cluster_class["clustering"][best_id].labels_            # 'label' est le nouveau nom de la colonne avec l'ancienne valeur du numéro de cluster
# mapping = {}
# i = 1
# for key, value in sorted_dict.items():
#     sorted_dict_cluster[key] = i
#     for l in range(len(cluster_class['Data']["label"])):
#         print("l=",l)
#         if cluster_class['Data'].index[l] == key:
#             print("i=",i)
#             mapping[cluster_class['Data']["label"].iloc[l]] = i
#     i+=1
# print(sorted_dict)
# print(mapping)
# cluster_class['Data']["clustering"] = cluster_class['Data']["label"].map(mapping)


reader = QBuildingsReader()
reader.establish_connection('Suisse')
qbuildings_data = {}
key_to_remove = []
for tr in typical_districts_data.index:
    print(tr)
    try:
        data_DB = reader.read_db(tr, nb_buildings=10000)
        qbuildings_data[tr] = gpd.GeoDataFrame.from_dict(data_DB['buildings_data']).transpose().reset_index().set_geometry("geometry")
    except:
        key_to_remove = key_to_remove + [tr]

for key in key_to_remove:
    typical_districts_data = typical_districts_data.drop(key)
    print(key)

# Convertir la colonne boundary en GeoSeries
boundary_series = gpd.GeoSeries(results["raw_data"]["geometry"])


## The for-loop is for plotting each typical district with building information
for i, tr in enumerate(typical_districts_data.index):
    data_to_plot = np.round(results["raw_data"][['rho_household', 'rho_industry', 'rho_service']].astype(float).loc[tr]*100, 0)
    data_to_plot.at["Transformer"] = tr
    data_to_plot.at["Cluster"] = results['raw_data']["cluster"].loc[tr]
    data_to_plot.at["N buildings"] = qbuildings_data[tr].__len__()
    data_to_plot.at["connectivity"] = results['raw_data']['connectivity level'].loc[tr]

    fig, ax = plt.subplots(1, 1)
    qbuildings_data[tr]["ERA"] = qbuildings_data[tr]["ERA"].astype(float)
    max = np.min([qbuildings_data[tr]["ERA"].max(), 10000])
    boundary_series.loc[[tr]].boundary.plot(ax=ax, color="black")
    qbuildings_data[tr].plot(column="ERA", legend=False, ax=ax, cmap='OrRd', vmax=max)
    
    # modification of the color bar to show a legend
    sm = plt.cm.ScalarMappable(
        cmap='OrRd', 
        norm=mpl.colors.Normalize(vmin=0, vmax=max)
    )
    cbar = fig.colorbar(sm, ax=ax, orientation='vertical', fraction=0.02, pad=0.1)
    cbar.set_label("ERA values") 

    # Debugging: Print the transformer and max value
    print(f"Transformer: {tr}, Max ERA: {max}")

    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    for spine in plt.gca().spines.values():
        spine.set_visible(False)
    cx.add_basemap(ax, crs="EPSG:2056")
    #add_basemap_with_retry(ax, crs="EPSG:2056")
    ax.legend([data_to_plot], bbox_to_anchor=(1.1, -0.1))
    fig.tight_layout()
    fig.savefig('figure/LAU_'+str(n)+'/LAU_'+str(n)+'_district'+str(tr)+'.pdf')
    plt.show()


## Plots the two city-scale maps, with typical districts and all of them
path_CH = path+"/plotting/CH_map.tif"
with rasterio.open(path_CH) as src:
    CH_map = src.read(1, masked=True)
plot_map_CH(results["raw_data"].loc[typical_districts_data.index], path+"/plotting", CH_map, show_n=True)       # plot uniquement la map avec seulement les typical districts et les numéros en rouge
plot_map_CH(results["raw_data"], path+"/plotting", CH_map)

print("End")








if False:
    data = pd.concat([results["Data"][["cluster", "ERA"]], data], axis=1).dropna()
    data = data.groupby(["cluster", "city"]).sum()
    data = data["ERA"].unstack(1).replace(np.nan, 0)
    data = np.round(data/data.sum()*100, 1)

    colors = ["#ffd980", "#FEA993",  "#ff6666", "#B22222", "#770001", "#1d3f5c", "#3573a6", "#74a7d2", "#b7d2e8"]
    bottom = 0
    for idx in data.index:
        plt.bar(data.columns, data.loc[idx], 0.5, label=idx, bottom=bottom, color=colors[int(idx)])
        bottom += data.loc[idx]
    plt.legend(bbox_to_anchor=(1.2, 1))
    plt.xticks(rotation=70)
    plt.tight_layout()
    plt.show()