######################################################################################################################################
#### File with multiple functions to plot mobility-related graphs, mainly aggregated modes, total demand.                         ####
#### The functions offer the possibility to choose the transformer, the typical period, the year and the scenario (PVHP or not)   ####
######################################################################################################################################


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from reho.plotting import plotting

# weekdays/ends list from scripts/examples/data/clustering/timestamp_Geneva_10_24_T_I_W.dat
weekdays = [2,5,7,8,9,10]
weekends = [1,3,4,6]

## Old function, not used for the final plots
def plot_PT(p, transformer, year):
    # 'ice_share_' is either set low, mid or high according to modalshares.csv
    t = np.arange(1,25,1)
    df = pd.read_pickle(f'../examples/results/7a_{transformer}_{year}.pickle')
    profiles = pd.read_csv(f'../../reho/data/mobility/PT_profiles/{transformer}_PT.csv')
    #df = pd.read_pickle(f'../examples/results/test_5bd/6a_{ice_share}.pickle')

    working_df = df['totex'][0]['df_Unit_t'].xs('Mobility', level='Layer')
    #working_df = df_Unit_t.xs('Mobility', level='Layer').xs('EV_district', level='Unit').xs(p, level='Period')
    pkm_ebus = working_df.xs('ElectricBus_district', level='Unit').xs(p, level='Period')['Units_supply']
    pkm_trolley = working_df.xs('TrolleyBus_district', level='Unit').xs(p, level='Period')['Units_supply']
    pkm_diesel = working_df.xs('DieselBus_district', level='Unit').xs(p, level='Period')['Units_supply']
    pkm_metro = working_df.xs('Metro_district', level='Unit').xs(p, level='Period')['Units_supply']

    demand_metro = 1.5 * profiles.loc[:,profiles.columns.str.contains("metro")]
    demand_bus = 1.31 * profiles.loc[:,profiles.columns.str.contains("bus")]

    fig1, ax1 = plt.subplots(figsize=(8, 5))
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    #fig3, ax3 = plt.subplots(figsize=(8, 5))

    # Plot for bus
    #ax1.fill_between(t, demand_bus, color='blue', alpha=0.3)
    ax1.plot(t, pkm_ebus+pkm_trolley+pkm_diesel, color='blue', label='bus usage')
    ax1.plot(t, demand_bus, color='blue', linestyle='--', label='bus demand')
    ax1.set_xlabel('Time')
    ax1.set_ylabel('pkm')
    ax1.legend()
    #ax1.set_title(f"PT demand profiles for typical period {p} and district {transformer}")

    # Plot for metro
    #ax2.fill_between(t, demand_metro, color='green', alpha=0.3)
    ax2.plot(t, pkm_metro, color='green', label='metro usage')
    ax2.plot(t, demand_metro, color='green', linestyle='--', label='metro demand')
    ax2.set_xlabel('Time')
    ax2.set_ylabel('pkm')
    ax2.legend()
    # ax2.set_title(f"PT maximum capacity for typical period {p} and district {transformer}, with {ice_share} ICE")
    # #ax2.set_title(f"Metro demand profiles and their maximum capacity for typical period {p} and district {transformer}")

    # Plot for join pkm_bus and pkm_metro
    #ax1.fill_between(t, demand_bus, color='blue', alpha=0.3)
    # ax3.plot(t, pkm_bus+pkm_metro, color='purple', label='bus+metro')
    # ax3.set_xlabel('Time')
    # ax3.set_ylabel('pkm')
    # ax3.legend()
    # ax3.set_title(f"Sum of PT demand profiles for typical period {p} and district {transformer}")

    #fig1.savefig(f'figure/district_{transformer}/pkm/pkm_PT.png')
    #fig2.savefig(f'figure/district_{transformer}/demand/demand_PT_{ice_share}.png')
    #fig3.savefig(f'figure/district_{transformer}/pkm/sumPT.png')
    plt.tight_layout()
    plt.show()
    
## Old function, not used for the final plots
def plot_cars(ice_share, p, transformer):
    # 'ice_share_' is either set low, mid or high according to modalshares.csv
    t = np.arange(1,25,1)
    df = pd.read_pickle(f'../examples/results/6a_{ice_share}.pickle')

    df_Unit_t = df['totex_1'][0]['df_Unit_t']
    working_df = df_Unit_t.xs('Mobility', level='Layer').xs('ICE_district', level='Unit').xs(p, level='Period')
    pkm_cars = working_df['Units_supply']

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(t, pkm_cars, color='brown', label='pkm_cars')
    ax.set_xlabel('Time')
    ax.set_ylabel('pkm')
    ax.legend()
    ax.set_title(f"Cars demand profiles for typical period {p} and district {transformer}, with {ice_share} ICE")

    fig.savefig(f'figure/district_{transformer}/pkm/pkm_cars_{ice_share}.png')
    plt.tight_layout()
    plt.show()

## Old function, not used for the final plots
def plot_EVs(ice_share, p, transformer):
    # 'ice_share_' is either set low, mid or high according to modalshares.csv
    t = np.arange(1,25,1)
    df = pd.read_pickle(f'../examples/results/6a_{ice_share}.pickle')

    df_Unit_t = df['totex_1'][0]['df_Unit_t']
    working_df = df_Unit_t.xs('Mobility', level='Layer').xs('EV_district', level='Unit').xs(p, level='Period')
    pkm_EVs = working_df['Units_supply']

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(t, pkm_EVs, color='orange', label='pkm_EVs')
    ax.set_xlabel('Time')
    ax.set_ylabel('pkm')
    ax.legend()
    ax.set_title(f"EVs demand profiles for typical period {p} and district {transformer}, with {ice_share} ICE")

    fig.savefig(f'figure/district_{transformer}/pkm/pkm_EVs_{ice_share}.png')
    plt.tight_layout()
    plt.show()

## Old function, not used for the final plots
def pkm_comparison(mode, p, transformer):
    t = np.arange(1,25,1)
    df_test = pd.read_pickle(f'../examples/results/6a_{transformer}_test.pickle')    
    df_low = pd.read_pickle(f'../examples/results/{transformer}/6a_low_{transformer}.pickle')
    df_mid = pd.read_pickle(f'../examples/results/{transformer}/6a_mid_{transformer}.pickle')
    df_high = pd.read_pickle(f'../examples/results/{transformer}/6a_high_{transformer}.pickle')

    df_Unit_t_test = df_test['totex_1'][0]['df_Unit_t']
    df_Unit_t_low = df_low['totex_1'][0]['df_Unit_t']
    df_Unit_t_mid = df_mid['totex_1'][0]['df_Unit_t']
    df_Unit_t_high = df_high['totex_1'][0]['df_Unit_t']

    df_demand = df_low['totex_1'][0]['df_Grid_t'].xs('Mobility', level='Layer').xs('Network', level='Hub').xs(p, level='Period')
    demand = df_demand['Domestic_energy']

    if mode == 'PT':
        fig1, ax1 = plt.subplots(figsize=(8, 5))
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        fig3, ax3 = plt.subplots(figsize=(8, 5))

        working_df_low = df_Unit_t_low.xs('Mobility', level='Layer').xs('EV_district', level='Unit').xs(p, level='Period')
        pkm_bus_low = working_df_low['pkm_PT_bus']
        pkm_metro_low = working_df_low['pkm_PT_metro']

        working_df_mid = df_Unit_t_mid.xs('Mobility', level='Layer').xs('EV_district', level='Unit').xs(p, level='Period')
        pkm_bus_mid = working_df_mid['pkm_PT_bus']
        pkm_metro_mid = working_df_mid['pkm_PT_metro']

        working_df_high = df_Unit_t_high.xs('Mobility', level='Layer').xs('EV_district', level='Unit').xs(p, level='Period')
        pkm_bus_high = working_df_high['pkm_PT_bus']
        pkm_metro_high = working_df_high['pkm_PT_metro']

        
        ## Plotting
        # Plot bus profiles comparison
        ax1.plot(t, pkm_bus_low, color='green', label='pkm_bus_low')
        ax1.plot(t, pkm_bus_mid, color='blue', label='pkm_bus_mid')
        ax1.plot(t, pkm_bus_high, color='red', label='pkm_bus_high')
        ax1.plot(t, demand, color='black', label='total demand')

        ax1.set_xlabel('Time (hours)')
        ax1.set_ylabel('pkm')
        ax1.legend()
        ax1.grid(True)
        if p in weekdays:
            ax1.set_title(f"Bus demand profiles comparison for typical period {p} and district {transformer} on a weekday")
            fig1.savefig(f'figure/{transformer}/comparison/bus_comp_weekday.png')
        else:
            ax1.set_title(f"Bus demand profiles comparison for typical period {p} and district {transformer} on a weekend")
            fig1.savefig(f'figure/{transformer}/comparison/bus_comp_weekend.png')


        # Plot metro profiles comparison
        ax2.plot(t, pkm_metro_low, color='green', label='pkm_metro_low')
        ax2.plot(t, pkm_metro_mid, color='blue', label='pkm_metro_mid')
        ax2.plot(t, pkm_metro_high, color='red', label='pkm_metro_high')
        ax2.plot(t, demand, color='black', label='total demand')

        ax2.set_xlabel('Time (hours)')
        ax2.set_ylabel('pkm')
        ax2.legend()
        ax2.grid(True)
        if p in weekdays:
            ax2.set_title(f"Metro demand profiles comparison for typical period {p} and district {transformer} on a weekday")
            fig2.savefig(f'figure/{transformer}/comparison/metro_comp_weekday.png')
        else:
            ax2.set_title(f"Metro demand profiles comparison for typical period {p} and district {transformer} on a weekend")
            fig2.savefig(f'figure/{transformer}/comparison/metro_comp_weekend.png')


        # Plot metro and bus profiles comparison
        ax3.plot(t, pkm_bus_low+pkm_metro_low, color='green', label='PT_low')
        ax3.plot(t, pkm_bus_mid+pkm_metro_mid, color='blue', label='PT_mid')
        ax3.plot(t, pkm_bus_high+pkm_metro_high, color='red', label='PT_high')
        ax3.plot(t, demand, color='black', label='total demand')

        ax3.set_xlabel('Time (hours)')
        ax3.set_ylabel('pkm')
        ax3.legend()
        ax3.grid(True)
        if p in weekdays:
            ax3.set_title(f"Sum of PT demand profiles comparison for typical period {p} and district {transformer} on a weekday")
            fig3.savefig(f'figure/{transformer}/comparison/sumPT_comp_weekday.png')
        else:
            ax3.set_title(f"Sum of PT demand profiles comparison for typical period {p} and district {transformer} on a weekend")
            fig3.savefig(f'figure/{transformer}/comparison/sumPT_comp_weekend.png')
        
        plt.tight_layout()
        plt.show()

    elif mode == 'ICE':
        fig1, ax1 = plt.subplots(figsize=(8, 5))

        working_df_low = df_Unit_t_low.xs('Mobility', level='Layer').xs('ICE_district', level='Unit').xs(p, level='Period')
        pkm_cars_low = working_df_low['Units_supply']

        working_df_mid = df_Unit_t_mid.xs('Mobility', level='Layer').xs('ICE_district', level='Unit').xs(p, level='Period')
        pkm_cars_mid = working_df_mid['Units_supply']

        working_df_high = df_Unit_t_high.xs('Mobility', level='Layer').xs('ICE_district', level='Unit').xs(p, level='Period')
        pkm_cars_high = working_df_high['Units_supply']

        ## Plotting
        # Plot cars profiles comparison
        ax1.plot(t, pkm_cars_low, color='green', label='pkm_cars_low')
        ax1.plot(t, pkm_cars_mid, color='blue', label='pkm_cars_mid')
        ax1.plot(t, pkm_cars_high, color='red', label='pkm_cars_high')
        ax1.plot(t, demand, color='black', label='total demand')

        ax1.set_xlabel('Time (hours)')
        ax1.set_ylabel('pkm')
        ax1.legend()
        ax1.grid(True)
        if p in weekdays:
            ax1.set_title(f"ICE cars demand profiles comparison for typical period {p} and district {transformer} on a weekday")
            fig1.savefig(f'figure/{transformer}/comparison/cars_comp_weekday.png')
        else:
            ax1.set_title(f"ICE cars demand profiles comparison for typical period {p} and district {transformer} on a weekend")
            fig1.savefig(f'figure/{transformer}/comparison/cars_comp_weekend.png')

        plt.tight_layout()
        plt.show()

    else : 
        fig1, ax1 = plt.subplots(figsize=(8, 5))

        working_df_low = df_Unit_t_low.xs('Mobility', level='Layer').xs('EV_district', level='Unit').xs(p, level='Period')
        pkm_EV_low = working_df_low['Units_supply']

        working_df_mid = df_Unit_t_mid.xs('Mobility', level='Layer').xs('EV_district', level='Unit').xs(p, level='Period')
        pkm_EV_mid = working_df_mid['Units_supply']

        working_df_high = df_Unit_t_high.xs('Mobility', level='Layer').xs('EV_district', level='Unit').xs(p, level='Period')
        pkm_EV_high = working_df_high['Units_supply']

        ## Plotting
        # Plot cars profiles comparison
        ax1.plot(t, pkm_EV_low, color='green', label='pkm_EV_low')
        ax1.plot(t, pkm_EV_mid, color='blue', label='pkm_EV_mid')
        ax1.plot(t, pkm_EV_high, color='red', label='pkm_EV_high')
        ax1.plot(t, demand, color='black', label='total demand')

        ax1.set_xlabel('Time (hours)')
        ax1.set_ylabel('pkm')
        ax1.legend()
        ax1.grid(True)
        if p in weekdays:
            ax1.set_title(f"EVs demand profiles comparison for typical period {p} and district {transformer} on a weekday")
            fig1.savefig(f'figure/{transformer}/comparison/EV_comp_weekday.png')

        else:
            ax1.set_title(f"EVs demand profiles comparison for typical period {p} and district {transformer} on a weekend")
            fig1.savefig(f'figure/{transformer}/comparison/EV_comp_weekend.png')


        plt.tight_layout()
        plt.show()



def pkm_aggregated_old(p, transformer):
    t = np.arange(1,25,1)

    df_low = pd.read_pickle(f'../examples/results/{transformer}/old/6a_low_{transformer}.pickle')
    df_mid = pd.read_pickle(f'../examples/results/{transformer}/old/6a_mid_{transformer}.pickle')
    df_high = pd.read_pickle(f'../examples/results/{transformer}/old/6a_high_{transformer}.pickle')
    
    df_demand = df_low['totex'][0]['df_Grid_t'].xs('Mobility', level='Layer').xs('Network', level='Hub').xs(p, level='Period')
    demand = df_demand['Domestic_energy']

    # PT variables
    working_df_low_PT = df_low['totex_1'][0]['df_Unit_t'].xs('Mobility', level='Layer').xs('EV_district', level='Unit').xs(p, level='Period')
    pkm_bus_low = working_df_low_PT['pkm_PT_bus']
    pkm_metro_low = working_df_low_PT['pkm_PT_metro']
    #pkm_train_low = working_df_low_PT['pkm_PT_train'], enlevé du plot aussi
    
    working_df_mid_PT = df_mid['totex_1'][0]['df_Unit_t'].xs('Mobility', level='Layer').xs('EV_district', level='Unit').xs(p, level='Period')
    pkm_bus_mid = working_df_mid_PT['pkm_PT_bus']
    pkm_metro_mid = working_df_mid_PT['pkm_PT_metro']

    working_df_high_PT = df_high['totex_1'][0]['df_Unit_t'].xs('Mobility', level='Layer').xs('EV_district', level='Unit').xs(p, level='Period')
    pkm_bus_high = working_df_high_PT['pkm_PT_bus']
    pkm_metro_high = working_df_high_PT['pkm_PT_metro']

    # Bike variables 
    working_df_low_bikes = df_low['totex_1'][0]['df_Unit_t'].xs('Mobility', level='Layer').xs('Bike_district', level='Unit').xs(p, level='Period')
    pkm_bike_low = working_df_low_bikes['Units_supply']
    working_df_mid_bikes = df_mid['totex_1'][0]['df_Unit_t'].xs('Mobility', level='Layer').xs('Bike_district', level='Unit').xs(p, level='Period')
    pkm_bike_mid = working_df_mid_bikes['Units_supply']
    working_df_high_bikes = df_high['totex'][0]['df_Unit_t'].xs('Mobility', level='Layer').xs('Bike_district', level='Unit').xs(p, level='Period')
    pkm_bike_high = working_df_high_bikes['Units_supply']

    working_df_low_Ebikes = df_low['totex_1'][0]['df_Unit_t'].xs('Mobility', level='Layer').xs('ElectricBike_district', level='Unit').xs(p, level='Period')
    pkm_ebike_low = working_df_low_Ebikes['Units_supply']
    working_df_mid_Ebikes = df_mid['totex_1'][0]['df_Unit_t'].xs('Mobility', level='Layer').xs('ElectricBike_district', level='Unit').xs(p, level='Period')
    pkm_ebike_mid = working_df_mid_Ebikes['Units_supply']
    working_df_high_Ebikes = df_high['totex'][0]['df_Unit_t'].xs('Mobility', level='Layer').xs('ElectricBike_district', level='Unit').xs(p, level='Period')
    pkm_ebike_high = working_df_high_Ebikes['Units_supply']



    # ICE variables
    working_df_low_cars = df_low['totex_1'][0]['df_Unit_t'].xs('Mobility', level='Layer').xs('ICE_district', level='Unit').xs(p, level='Period')
    pkm_cars_low = working_df_low_cars['Units_supply']

    working_df_mid_cars = df_mid['totex_1'][0]['df_Unit_t'].xs('Mobility', level='Layer').xs('ICE_district', level='Unit').xs(p, level='Period')
    pkm_cars_mid = working_df_mid_cars['Units_supply']

    working_df_high_cars = df_high['totex'][0]['df_Unit_t'].xs('Mobility', level='Layer').xs('ICE_district', level='Unit').xs(p, level='Period')
    pkm_cars_high = working_df_high_cars['Units_supply']

    # EV variables 
    working_df_low_EV = df_low['totex_1'][0]['df_Unit_t'].xs('Mobility', level='Layer').xs('EV_district', level='Unit').xs(p, level='Period')
    pkm_EV_low = working_df_low_EV['Units_supply']

    working_df_mid_EV = df_mid['totex_1'][0]['df_Unit_t'].xs('Mobility', level='Layer').xs('EV_district', level='Unit').xs(p, level='Period')
    pkm_EV_mid = working_df_mid_EV['Units_supply']

    working_df_high_EV = df_high['totex'][0]['df_Unit_t'].xs('Mobility', level='Layer').xs('EV_district', level='Unit').xs(p, level='Period')
    pkm_EV_high = working_df_high_EV['Units_supply']

    # working_df_low_charger = df_low['totex_1'][0]['df_Unit_t'].xs('Electricity', level='Layer').xs('EV_charger_district', level='Unit').xs(p, level='Period')
    # pkm_charger_low = working_df_low_charger['Units_supply']+working_df_low_charger['Units_demand']

    # Plot
    data_low = np.array([(pkm_bike_low+pkm_ebike_low), (pkm_bus_low+pkm_metro_low), pkm_cars_low, pkm_EV_low])
    data_mid = np.array([(pkm_bike_mid+pkm_ebike_mid), (pkm_bus_mid+pkm_metro_mid), pkm_cars_mid, pkm_EV_mid])
    data_high = np.array([(pkm_bike_high+pkm_ebike_high), (pkm_bus_high+pkm_metro_high), pkm_cars_high, pkm_EV_high])

    colors = ['lightskyblue','mediumpurple','grey','green', 'black']#,'grey']
    
    fig0, ax0 = plt.subplots(figsize=(8, 5))
    fig1, ax1 = plt.subplots(figsize=(8, 5))
    #fig2, ax2 = plt.subplots(figsize=(8, 5))
    #fig3, ax3 = plt.subplots(figsize=(8, 5))

    # To plot the demand only
    ax0.plot(t, demand)

    ax0.set_xlabel('t (hours)')
    ax0.set_ylabel('pkm')
    ax0.grid(True)
    if p in weekdays:
        ax0.set_title('Total weekday demand for mobility in pkm')
        #fig0.savefig(f'./figure/{transformer}/demand/demand_weekday.png')
    else:
        ax0.set_title('Total weekend demand for mobility in pkm')
        #fig0.savefig(f'./figure/{transformer}/demand/demand_weekend.png')

    # # Plot for low ICE share
    # ax1.stackplot(t, data_low, labels=['Bikes','PT','ICEs','EVs'], colors=colors)
    # ax1.plot(t, demand, label='total_demand', color='black')

    # ax1.set_xlabel('t (hours)')
    # ax1.set_ylabel('pkm')
    # ax1.grid(True)
    # ax1.legend()
    # if p in weekdays:
    #     ax1.set_title(f'Distribution of transportation modes on a weekday for district {transformer}, low ICE boundary')
    #     fig1.savefig(f'./figure/{transformer}/aggregated/aggregated_weekday_low.png')
    # else:
    #     ax1.set_title(f'Distribution of transportation modes on a weekend for district {transformer}, low ICE boundary')
    #     fig1.savefig(f'./figure/{transformer}/aggregated/aggregated_weekend_low.png')


    # # Plot for mid ICE share
    # ax2.stackplot(t, data_mid, labels=['Bikes','PT','ICES','EVs','total demand'], colors=colors)
    # ax2.plot(t, demand, label='total_demand', color='black')

    # ax2.set_xlabel('t (hours)')
    # ax2.set_ylabel('pkm')
    # ax2.grid(True)
    # ax2.legend()
    # if p in weekdays:
    #     ax2.set_title(f'Distribution of transportation modes on a weekday for district {transformer}, mid ICE boundary')
    #     fig2.savefig(f'./figure/{transformer}/aggregated/aggregated_weekday_mid.png')
    # else:
    #     ax2.set_title(f'Distribution of transportation modes on a weekend for district {transformer}, mid ICE boundary')
    #     fig2.savefig(f'./figure/{transformer}/aggregated/aggregated_weekend_mid.png')
    

    # # Plot for high ICE share
    # ax3.stackplot(t, data_high, labels=['Bikes','PT','ICEs','EVs','total demand'], colors=colors)
    # ax3.plot(t, demand, label='total_demand', color='black')

    # ax3.set_xlabel('t (hours)')
    # ax3.set_ylabel('pkm')
    # ax3.grid(True)
    # ax3.legend()
    # if p in weekdays:
    #     ax3.set_title(f'Distribution of transportation modes on a weekday for district {transformer}, high ICE boundary')
    #     fig3.savefig(f'./figure/{transformer}/aggregated/aggregated_weekday_high.png')
    # else:
    #     ax3.set_title(f'Distribution of transportation modes on a weekend for district {transformer}, high ICE boundary')
    #     fig3.savefig(f'./figure/{transformer}/aggregated/aggregated_weekend_high.png')
     
    plt.tight_layout()
    plt.show()

    # plt.figure(figsize=(12,8))
    # profiles_input = pd.read_csv("../../reho/data/mobility/dailyprofiles.csv", index_col=0)
    # for colonne in profiles_input.columns:  
    #     plt.plot(t, profiles_input[colonne], label=colonne)

    # plt.legend()
    # plt.show()



def pkm_aggregated(p, transformer, year, pvhp=True):
    t = np.arange(1,25,1)
    #df = pd.read_pickle(f'../examples/results/7a_{transformer}_{year}_relax.pickle')

    if not pvhp:
        df = pd.read_pickle(f'../examples/results/{transformer}/{year}/noPVHP/7a_{transformer}_{year}_no_PVHP.pickle')
    else:
        df = pd.read_pickle(f'../examples/results/{transformer}/{year}/7a_{transformer}_{year}.pickle')

    df_demand = df['totex'][0]['df_Grid_t'].xs('Mobility', level='Layer').xs('Network', level='Hub').xs(p, level='Period')
    demand = df_demand['Domestic_energy']

    # PT variables
    working_df_trolley = df['totex'][0]['df_Unit_t'].xs('Mobility', level='Layer').xs('TrolleyBus_district', level='Unit').xs(p, level='Period')
    working_df_ebus = df['totex'][0]['df_Unit_t'].xs('Mobility', level='Layer').xs('ElectricBus_district', level='Unit').xs(p, level='Period')
    working_df_diesel = df['totex'][0]['df_Unit_t'].xs('Mobility', level='Layer').xs('DieselBus_district', level='Unit').xs(p, level='Period')
    working_df_metro = df['totex'][0]['df_Unit_t'].xs('Mobility', level='Layer').xs('Metro_district', level='Unit').xs(p, level='Period')

    pkm_trolley = working_df_trolley['Units_supply'].fillna(0)
    pkm_ebus = working_df_ebus['Units_supply'].fillna(0)
    pkm_diesel = working_df_diesel['Units_supply'].fillna(0)
    pkm_metro = working_df_metro['Units_supply'].fillna(0)


    # Bike variables
    working_df_bikes = df['totex'][0]['df_Unit_t'].xs('Mobility', level='Layer').xs('Bike_district', level='Unit').xs(p, level='Period')
    working_df_Ebikes = df['totex'][0]['df_Unit_t'].xs('Mobility', level='Layer').xs('ElectricBike_district', level='Unit').xs(p, level='Period')

    pkm_bike = working_df_bikes['Units_supply']
    pkm_ebike = working_df_Ebikes['Units_supply']


    # ICE variables
    working_df_cars = df['totex'][0]['df_Unit_t'].xs('Mobility', level='Layer').xs('ICE_district', level='Unit').xs(p, level='Period')
    pkm_cars = working_df_cars['Units_supply']


    # EV variables 
    working_df_EV = df['totex'][0]['df_Unit_t'].xs('Mobility', level='Layer').xs('EV_district', level='Unit').xs(p, level='Period')
    pkm_EV = working_df_EV['Units_supply']


    # Plot
    #data_demand = np.array([(pkm_bike+pkm_ebike)/demand, (pkm_trolley+pkm_ebus+pkm_diesel+pkm_metro)/demand, pkm_cars/demand, pkm_EV/demand])
    data = np.array([(pkm_bike+pkm_ebike), (pkm_trolley+pkm_ebus+pkm_diesel+pkm_metro), pkm_cars, pkm_EV])

    colors = ['lightskyblue','mediumpurple','grey','green', 'black']
    
    fig0, ax0 = plt.subplots(figsize=(8, 5))
    fig1, ax1 = plt.subplots(figsize=(8, 5))

    # To plot the demand only
    ax0.plot(t, demand)

    ax0.set_xlabel('t (hours)')
    ax0.set_ylabel('Mobility demand (pkm)')
    ax0.grid(True)
    if pvhp:
        if p in weekdays:
            ax0.set_title('Total weekday demand for mobility in pkm')
            #fig0.savefig(f'./figure/demand_weekday.png')
        else:
            ax0.set_title('Total weekend demand for mobility in pkm')
            #fig0.savefig(f'./figure/demand_weekend.png')
    else:
        if p in weekdays:
            ax0.set_title('Total weekday demand for mobility in pkm')
            #fig0.savefig(f'./figure/{transformer}/{year}/noPVHP/demand/demand_weekday.png')
        else:
            ax0.set_title('Total weekend demand for mobility in pkm')
            #fig0.savefig(f'./figure/{transformer}/{year}/noPVHP/demand/demand_weekend.png')

    # Plotting the modes
    ax1.stackplot(t, data, labels=['Bikes','PT','ICEs','EVs'], colors=colors)
    #ax1.plot(t, demand, label='total_demand', color='black')

    ax1.set_xlabel('t (hours)')
    ax1.set_ylabel('Mobility demand (pkm)')
    ax1.grid(True)
    ax1.legend()

    if pvhp:
        if p in weekdays:
            ax1.set_title(f'Distribution of transportation modes on a weekday in {year} for district {transformer}')
            fig1.savefig(f'./figure/{transformer}/{year}/aggregated/aggregated_weekday.png')
        else:
            ax1.set_title(f'Distribution of transportation modes on a weekend in {year} for district {transformer}')
            fig1.savefig(f'./figure/{transformer}/{year}/aggregated/aggregated_weekend.png')
    else:
        if p in weekdays:
            ax1.set_title(f'Distribution of transportation modes on a weekday in {year} for district {transformer}')
            fig1.savefig(f'./figure/{transformer}/{year}/noPVHP/aggregated/aggregated_weekday.png')
        else:
            ax1.set_title(f'Distribution of transportation modes on a weekend in {year} for district {transformer}')
            fig1.savefig(f'./figure/{transformer}/{year}/noPVHP/aggregated/aggregated_weekend.png')

    plt.tight_layout()
    plt.show()


## Prefer the cost function in 7a_plotting.py
def plot_costs(transformer, year, pvhp=True):
    if not pvhp:
        df = pd.read_pickle(f'../examples/results/{transformer}/{year}/noPVHP/7a_{transformer}_{year}_no_PVHP.pickle')
    else:
        df = pd.read_pickle(f'../examples/results/{transformer}/{year}/7a_{transformer}_{year}.pickle')

    plotting.plot_performance(df, plot='costs', indexed_on='Pareto_ID', label='EN_long', title=f'{transformer}_{year}').show()


def plot_total_mobility():
    t = np.arange(1,25,1)
    file = pd.read_csv("../../reho/data/mobility/dailyprofiles.csv")

    day = file.loc[:,file.columns.str.contains("demwdy")]
    we = file.loc[:,file.columns.str.contains("demwnd")]

    fig1, ax1 = plt.subplots(figsize=(8, 5))
    fig2, ax2 = plt.subplots(figsize=(8, 5))

    ax1.plot(t, day)
    ax1.set_xlabel("hours")
    #ax1.set_ylabel("Mobility (pkm)")
    ax1.yaxis.set_ticks([])  
    ax1.yaxis.set_ticklabels([])
    ax1.set_title("Weekday")

    ax2.plot(t, we)
    ax2.set_xlabel("hours")
    #ax2.set_ylabel("Mobility (pkm)")
    ax2.yaxis.set_ticks([])  
    ax2.yaxis.set_ticklabels([])
    ax2.set_title("Weekend")

    fig1.tight_layout()
    fig1.savefig("figure/weekday_mobility")
    fig2.tight_layout()
    fig2.savefig("figure/weekend_mobility")

    plt.show()


## Function aiming at plotting all the graphs for Lausanne, but done one by one in the 'main' instead
def plot_Lausanne(cluster):
    for x in cluster:
        for year in [2024]:
            pkm_aggregated(weekdays[0], x, year)
            pkm_aggregated(weekends[0], x, year)
            #plot_costs(x, year)
        # df_low = pd.read_pickle(f'../examples/results/{x}/6a_low_{x}.pickle')
        # plotting.plot_performance(df_low, plot='costs', indexed_on='Pareto_ID', label='EN_long', title='Economical performance - low').show()
        # df_mid = pd.read_pickle(f'../examples/results/{x}/6a_mid_{x}.pickle')
        # plotting.plot_performance(df_mid, plot='costs', indexed_on='Pareto_ID', label='EN_long', title='Economical performance - mid').show()
        # df_high = pd.read_pickle(f'../examples/results/{x}/6a_high_{x}.pickle')
        # plotting.plot_performance(df_high, plot='costs', indexed_on='Pareto_ID', label='EN_long', title='Economical performance - high').show()

   




if __name__ == '__main__':
    #plot_PT(2, 3195, 2050)

    #pkm_comparison('EV', 1, 3246)
    #pkm_aggregated(1, 10680, 2024)
    #pkm_aggregated(2, 10680, 2024)

    cluster_list = [3195, 3217, 3230, 10481, 10491]
    #plot_Lausanne(cluster_list)
    # pkm_aggregated(weekdays[0],3230,2024)
    # pkm_aggregated(weekends[0],3230,2024)
    #plot_total_mobility()

    for year in [2024,2030,2050]:
        #plot_costs(3230,year,pvhp=False)
        pkm_aggregated(1,3230,year,pvhp=True)
        pkm_aggregated(2,3230,year,pvhp=True)

