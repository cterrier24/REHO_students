"""
Utility functions for Geneva scenarios.
"""
import math
import pandas as pd


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

def get_renter_param(base_path: str, neighborhood_type: str, ch: bool = False) -> pd.Series:
    """
    Compute the renter_ref series for a given neighborhood scenario.

    Parameters:
    - base_path: str, the root directory containing the 'scripts/examples/results' subfolder.
    - neighborhood_type: str, one of the scenario identifiers (e.g., 'Center', 'Villa', 'Rural').

    Returns:
    - pd.Series named 'renter_ref', indexed by building/hub labels, with computed cost allocations.

    Raises:
    - FileNotFoundError if the pickle file does not exist.
    """
    # Build the full pickle file path
    if ch:
        file_path = (
            f"results/CH/9a_{neighborhood_type}_TOTEX_wo_El.pickle"
        )
    else:
        file_path = (
            f"results/9a_{neighborhood_type}_TOTEX_wo_El.pickle"
        )
    try:
        data = pd.read_pickle(file_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find file: {file_path}")

    ERA = data['actors'][0]['df_Buildings']['ERA']
    df_econ = data['actors'][0]['df_Economics']
    reinf = (
        data['actors'][0]['df_Grid']
            .xs('Network')
            .xs('Electricity')['ReinforcementCost']
    )

    renter_series = pd.Series(index=ERA.index, name="renter_ref")
    total_era = ERA.sum()

    for hub in ERA.index:
        net_costs = (
            df_econ
            .xs('Network', level='Hub', axis=0)
            .xs('costs')
        )
        local_costs = (
            df_econ
            .xs(hub, level='Hub', axis=0)
            .xs('costs')
        )
        weight = ERA[hub] / total_era
        renter_series[hub] = (
            net_costs['investment']['ICE_district'] * weight
            + local_costs['investment'].get('NG_Boiler', 0)
            + local_costs['operation'].get('costs_Electricity', 0)
            + net_costs['operation']['costs_Gasoline'] * weight
            + local_costs['operation'].get('costs_NaturalGas', 0)
            + reinf * weight
            + data['actors'][0]['df_Unit']['Costs_Unit_inv'][f'WaterTankDHW_{hub}']
            + data['actors'][0]['df_Performance']['Cost_supply_district_mobility'][hub]
        )

    return renter_series