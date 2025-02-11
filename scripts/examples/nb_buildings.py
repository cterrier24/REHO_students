from reho.model.reho import *
import math

def remove_nan_QBuilding(buildings_data):
    for bui in buildings_data["buildings_data"]:
        bui_class = buildings_data["buildings_data"][bui]["id_class"]
        buildings_data["buildings_data"][bui]["id_class"] = buildings_data["buildings_data"][bui]["id_class"].replace("nan", "II")
        buildings_data["buildings_data"][bui]["id_class"] = buildings_data["buildings_data"][bui]["id_class"].replace("VIII", "III")
        buildings_data["buildings_data"][bui]["ratio"] = buildings_data["buildings_data"][bui]["ratio"].replace("nan", "0.0")
        if bui_class != buildings_data["buildings_data"][bui]["id_class"]:
            print(bui, "had nan class and was", bui_class)
        if math.isnan(buildings_data["buildings_data"][bui]["U_h"]):
            buildings_data["buildings_data"][bui]["U_h"] = 0.00181
        if math.isnan(buildings_data["buildings_data"][bui]["HeatCapacity"]):
            buildings_data["buildings_data"][bui]["HeatCapacity"] = 120
        if math.isnan(buildings_data["buildings_data"][bui]["T_comfort_min_0"]):
            buildings_data["buildings_data"][bui]["T_comfort_min_0"] = 20
    return buildings_data

#def building_to_excel(file):


if __name__ == '__main__':
    qbuildings_data = {}
    key_except= []
    N_buildings = []
    xls = pd.ExcelFile("../maxime/data/mixture_LAU_9.xlsx")
    df = pd.read_excel(xls, sheet_name="raw_data")

    reader = QBuildingsReader()
    reader.establish_connection('Suisse')
    
    for i in range(len(df)):
        tr = int(df['id'].iloc[i])
        try:
            data_DB = reader.read_db(tr, nb_buildings=10000)
            qbuildings_data[tr] = gpd.GeoDataFrame.from_dict(data_DB['buildings_data']).transpose().reset_index().set_geometry("geometry")
            #qbuildings_data = remove_nan_QBuilding(qbuildings_data)
            N_buildings.append(qbuildings_data[tr].__len__())
        except:
            key_except.append(tr)
            N_buildings.append(0)

        #print(i*100/93)
        #N_buildings.append(qbuildings_data[tr].__len__())
        # qbuildings_data = remove_nan_QBuilding(qbuildings_data)  

    df["N_buildings"] = N_buildings

    other_tabs = {sheet: pd.read_excel(xls, sheet_name=sheet) for sheet in xls.sheet_names if sheet != "raw_data"}

    with pd.ExcelWriter("../maxime/data/mixture_LAU_9_bd.xlsx", engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="raw_data", index=False)
        
        for sheet, data in other_tabs.items():
            data.to_excel(writer, sheet_name=sheet, index=False)



    
