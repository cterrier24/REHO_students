######################################################################################################################################
#### Modify the pickle file concerning electricity : the new consumption due to mobility are added to the file                    ####
######################################################################################################################################


import pandas as pd
import numpy as np

def compute_index(outside=False):
    if outside:
        df = pd.read_pickle(f'../examples/results/3230/2024/7a_3230_2024.pickle')
    else:
        df = pd.read_pickle(f'../../../scripts/examples/results/3230/2024/7a_3230_2024.pickle')       # no matter the year anf the transformer since the temporal clustering stays the same

    tab = df['totex'][0]['df_Index']
    index = dict()
    for p in range(1,11):
        index[p] = len(tab[tab['PeriodOfYear']==p])/24
    
    return index


def add_consumption(df, outside=False):
    working_df = df['totex'][0]['df_Unit_t'].xs('Electricity', level='Layer')
    diesel_df = df['totex'][0]['df_Unit_t'].xs('Mobility', level='Layer')

    E_trolley = dict()
    E_ebus = dict()
    E_metro = dict()
    E_EV_charger = dict()
    E_EV_supply = dict()
    E_diesel = dict()


    for p in range(1,11):
        E_trolley[p] = 24*[0]
        E_ebus[p] = 24*[0]
        E_metro[p] = 24*[0]
        E_EV_charger[p] = 24*[0]
        E_EV_supply[p] = 24*[0]
        E_diesel[p] = 24*[0]


    for p in range(1,11):
        E_trolley[p] = working_df.xs('TrolleyBus_district', level='Unit').xs(p, level='Period')['trolley_demand']
        E_ebus[p] = working_df.xs('ElectricBus_district', level='Unit').xs(p, level='Period')['ebus_demand']
        E_metro[p] = working_df.xs('Metro_district', level='Unit').xs(p, level='Period')['metro_demand']
        E_EV_charger[p] = working_df.xs('EV_charger_district', level='Unit').xs(p, level='Period')['Units_demand']
        E_EV_supply[p] = working_df.xs('EV_charger_district', level='Unit').xs(p, level='Period')['Units_supply']
        E_diesel[p] = diesel_df.xs('DieselBus_district', level='Unit').xs(p, level='Period')['Units_supply'] * 0.30237      # same conversion factor as for ICE_district

    index = compute_index(outside)
    Trolley_cons = []
    Ebus_cons = []
    Metro_cons = []
    Diesel_cons = []
    for p in range(1,11):
        trolley_temp = 0
        ebus_temp = 0
        metro_temp = 0
        diesel_temp = 0
        for h in range(1,25):
            trolley_temp += E_trolley[p][h]
            ebus_temp += E_ebus[p][h]
            metro_temp += E_metro[p][h]
            diesel_temp += E_diesel[p][h]
        Trolley_cons.append(trolley_temp * index[p])
        Ebus_cons.append(ebus_temp * index[p])
        Metro_cons.append(metro_temp * index[p])
        Diesel_cons.append(diesel_temp * index[p])

    # annual consumptions in MWh
    annuals = [np.sum(Trolley_cons)/1000, np.sum(Ebus_cons)/1000, np.sum(Metro_cons)/1000, np.sum(Diesel_cons)/1000]            
    
    # adding to the dataframe
    row_trolley = pd.DataFrame([[annuals[0], 0]], columns=df['totex'][0]['df_Annuals'].columns, index=pd.MultiIndex.from_tuples([('Electricity', 'TrolleyBus_district')], names=['Layer', 'Hub']))
    row_ebus = pd.DataFrame([[annuals[1], 0]], columns=df['totex'][0]['df_Annuals'].columns, index=pd.MultiIndex.from_tuples([('Electricity', 'ElectricBus_district')], names=['Layer', 'Hub']))
    row_metro = pd.DataFrame([[annuals[2], 0]], columns=df['totex'][0]['df_Annuals'].columns, index=pd.MultiIndex.from_tuples([('Electricity', 'Metro_district')], names=['Layer', 'Hub']))
    row_diesel = pd.DataFrame([[annuals[3], 0]], columns=df['totex'][0]['df_Annuals'].columns, index=pd.MultiIndex.from_tuples([('FossilFuel', 'DieselBus_district')], names=['Layer', 'Hub']))

    df['totex'][0]['df_Annuals'] = pd.concat([df['totex'][0]['df_Annuals'], row_trolley])
    df['totex'][0]['df_Annuals'] = pd.concat([df['totex'][0]['df_Annuals'], row_ebus])
    df['totex'][0]['df_Annuals'] = pd.concat([df['totex'][0]['df_Annuals'], row_metro])
    df['totex'][0]['df_Annuals'] = pd.concat([df['totex'][0]['df_Annuals'], row_diesel])

    # modifying the electricity import to match the new values
    df['totex'][0]['df_Annuals'].loc[('Electricity', 'Network'), 'Supply_MWh'] += annuals[0] + annuals[1] + annuals[2]



    # # modifying the values in the 'Mobility' layer to manage to properly add flows on the Sankey
    # df['totex'][0]['df_Annuals'].loc[('Mobility', 'TrolleyBus_district'), 'Supply_MWh'] = annuals[0]
    # df['totex'][0]['df_Annuals'].loc[('Mobility', 'ElectricBus_district'), 'Supply_MWh'] = annuals[1]
    # df['totex'][0]['df_Annuals'].loc[('Mobility', 'Metro_district'), 'Supply_MWh'] = annuals[2]
    # df['totex'][0]['df_Annuals'].loc[('Mobility', 'DieselBus_district'), 'Supply_MWh'] = annuals[3]




    
if __name__ =='__main__':
    df = pd.read_pickle(f'../../../scripts/examples/results/3230/2030/7a_3230_2030.pickle')
    add_consumption(df)

