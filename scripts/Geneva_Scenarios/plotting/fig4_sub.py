"""
Sensitivity Analysis Visualization for Subsidy Distributions

This script generates publication-quality heatmap visualizations showing the sensitivity
of subsidy distributions (total, landlord, ECM) to interest rates and tenant affordability
across different urban typologies.

Author: [Your Name]
Date: 2025-10-15
"""

# Standard library imports
import os
import re
from typing import Tuple

# Third-party imports
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.interpolate import griddata


# =============================================================================
# CONFIGURATION
# =============================================================================

# File paths
DATA_PATH = "../results/SA"
OUTPUT_DIR = "plots"

# File selection parameters
FILE_PREFIX = "9d"
FILE_EXTENSION = ".pickle"
FILENAME_PATTERN = re.compile(
    r"9d_(?P<group>[A-Za-z\-]+)_[a-z]+_i(?P<i>[0-9.]+)_r(?P<r>[0-9.]+).pickle"
)

# Energy Reference Area (ERA) by urban typology [m²]
ERA_MAPPING = {
    "Urban": 231225,
    "Low-rise": 30827,
    "High-rise": 124379,
    "Countryside": 23956,
}

# Normalization factors
NORMALIZATION_FACTOR = 46  # capita
EV_BUILDINGS_FACTOR = 70

# Figure configuration
FIGURE_CONFIG = {
    "height": 900,
    "width": 1300,
    "horizontal_spacing": 0.08,
    "vertical_spacing": 0.08,
    "font_size": 14,
    "colorbar_font_size": 12,
    "title_font_size": 14,
    "axis_font_size": 12,
    "tick_font_size": 10,
    "template": "plotly_white",
    "font_family": "Arial, sans-serif",  # Use "Times New Roman" for journals
    "show_grid": True,
    "gridcolor": "rgba(128,128,128,0.2)",
    "show_contours": True,  # Add contour lines
    "contour_color": "rgba(0,0,0,0.3)",
    "n_contours": 5,
}

# Grid interpolation parameters
GRID_RESOLUTION = 500
INTERPOLATION_METHOD = "cubic"

# Color scales for subsidy metrics (perceptually uniform, colorblind-friendly)
COLOR_SCALES = {
    "Total Subsidies<br>[CHF/cap/yr]": [
        [0.0, "#f7fcf5"],   # Very light green
        [0.2, "#c7e9c0"],   # Pale green
        [0.4, "#74c476"],   # Light green
        [0.6, "#31a354"],   # Medium green
        [0.8, "#006d2c"],   # Dark green
        [1.0, "#00441b"]    # Deep green
    ],
    "Owner Subsidies<br>[CHF/cap/yr]": [
        [0.0, "#fff5f0"],   # Very light red
        [0.2, "#fee0d2"],   # Pale red
        [0.4, "#fc9272"],   # Light red
        [0.6, "#de2d26"],   # Medium red
        [0.8, "#a50f15"],   # Dark red
        [1.0, "#67000d"]    # Deep red
    ],
    "ECM Subsidies<br>[CHF/cap/yr]": [
        [0.0, "#f7fbff"],   # Very light blue
        [0.2, "#deebf7"],   # Pale blue
        [0.4, "#9ecae1"],   # Light blue
        [0.6, "#4292c6"],   # Medium blue
        [0.8, "#2171b5"],   # Dark blue
        [1.0, "#08519c"]    # Deep blue
    ],
}

# Output files
OUTPUT_FILES = {
    "html": "plot_sensi_sub.html",
    "pdf": "fig4_sensi_sub.pdf",
}


# =============================================================================
# DATA LOADING AND PROCESSING
# =============================================================================

def load_sensitivity_files(data_path: str) -> pd.DataFrame:
    all_files = os.listdir(data_path)
    files_9d = [f for f in all_files if f.startswith(FILE_PREFIX) and f.endswith(FILE_EXTENSION)]

    records = []
    for fname in files_9d:
        match = FILENAME_PATTERN.search(fname)
        if match:
            group = match.group("group")
            i_val = float(match.group("i"))
            r_val = float(match.group("r"))
            records.append({
                "Group": group,
                "Interest Rate": i_val,
                "Tenants Affordability": r_val,
                "File": fname
            })

    return pd.DataFrame(records)


def extract_metrics_from_file(file_name: str, data_path: str) -> Tuple:
    # Determine Energy Reference Area from file name
    era = None
    for group_name, era_value in ERA_MAPPING.items():
        if group_name in file_name:
            era = era_value
            break

    if era is None:
        raise ValueError(f"Unknown urban typology in file: {file_name}")

    # Load data
    file_path = os.path.join(data_path, file_name)
    df_pickle = pd.read_pickle(file_path)

    # Extract actor performance data
    actor_data = df_pickle['actors'][0]
    perf = actor_data['df_Performance']
    kpis = actor_data['df_KPIs']
    units = actor_data['df_Unit']

    # Calculate subsidies [CHF/cap/year]
    owner_subsidies = perf['owner_subsidies'].sum() / era * NORMALIZATION_FACTOR
    renter_subsidies = perf['renter_subsidies'].sum() / era * NORMALIZATION_FACTOR
    ecm_subsidies = perf['ECM_subsidies']['Network'] / era * NORMALIZATION_FACTOR
    total_subsidies = owner_subsidies + renter_subsidies + ecm_subsidies

    # Calculate GWP [tCO2/cap/year]
    gwp_construction = perf["GWP_constr"]["Network"]
    gwp_operation = perf["GWP_op"]["Network"]
    gwp_total = (gwp_construction + gwp_operation) / era * NORMALIZATION_FACTOR / 1000 + 5.6/10/1.6

    # Calculate investment costs [CHF/cap/year]
    total_investment = perf['Costs_inv'].sum() / era * NORMALIZATION_FACTOR
    ev_charger_cost = units['Costs_Unit_inv']['EV_charger_district'] / era * NORMALIZATION_FACTOR
    ev_vehicle_cost = units['Costs_Unit_inv']['EV_district'] / era * NORMALIZATION_FACTOR
    investment_excl_ev = total_investment - ev_charger_cost - ev_vehicle_cost

    # Extract KPIs
    self_sufficiency = kpis['SS']['Network']  # [%]
    self_consumption = kpis['SC']['Network']  # [%]
    totex = kpis['opex_m2']['Network'] * NORMALIZATION_FACTOR  # [CHF/cap/year]

    # Extract technology installations
    units_mult = units["Units_Mult"]
    pv_installation = units_mult[units_mult.index.str.contains("PV")].sum() / era * NORMALIZATION_FACTOR
    battery_installation = units_mult[units_mult.index.str.contains("Battery")].sum() / era * NORMALIZATION_FACTOR
    ev_availability = units_mult[units_mult.index.str.contains("EV_district")].sum() / EV_BUILDINGS_FACTOR / era * NORMALIZATION_FACTOR

    return (
        total_subsidies, gwp_total, pv_installation, investment_excl_ev,
        self_sufficiency, totex, battery_installation,
        owner_subsidies, renter_subsidies, ecm_subsidies,
        self_consumption, ev_availability
    )


def process_all_files(data_path: str) -> pd.DataFrame:
    # Load file metadata
    df_params = load_sensitivity_files(data_path)

    # Define metric column names
    metric_columns = [
        "Total Subsidies<br>[CHF/cap/yr]",
        "GWP [tCO2/cap/yr]",
        "PV Installation [kW/cap]",
        "Total Investment [CHF/cap/year]",
        "SS [%]",
        "TOTEX per capita [CHF/cap/yr]",
        "Battery Installation [kWh/cap]",
        "Owner Subsidies<br>[CHF/cap/yr]",
        "Renter Subsidies<br>[CHF/cap/yr]",
        "ECM Subsidies<br>[CHF/cap/yr]",
        "SC [%]",
        "EV [vehicles/cap]"
    ]

    # Extract metrics from all files
    df_params[metric_columns] = (
        df_params["File"]
        .apply(lambda fname: extract_metrics_from_file(fname, data_path))
        .apply(pd.Series)
    )

    return df_params


# =============================================================================
# VISUALIZATION
# =============================================================================

def create_interpolated_grid(x: np.ndarray, y: np.ndarray, z: np.ndarray) -> Tuple:
    xi = np.linspace(x.min(), x.max(), GRID_RESOLUTION)
    yi = np.linspace(y.min(), y.max(), GRID_RESOLUTION)
    XI, YI = np.meshgrid(xi, yi)

    # Interpolate using cubic method
    ZI = griddata((x, y), z, (XI, YI), method=INTERPOLATION_METHOD)

    # Clip negative values (non-physical)
    ZI = np.clip(ZI, a_min=0, a_max=None)

    return xi, yi, ZI


def create_sensitivity_heatmap(df_params: pd.DataFrame) -> go.Figure:
    # Define urban typologies and metrics to visualize
    urban_typologies = ["Urban", "Low-rise", "High-rise", "Countryside"]

    # Panel labels for scientific publications
    panel_labels = ["(a)", "(b)", "(c)", "(d)"]

    # Subsidy metrics with improved labels and row numbers
    metrics_to_plot = {
        "Total Subsidies<br>[CHF/cap/yr]": {"row": 1, "label": "Total Subsidies"},
        "Owner Subsidies<br>[CHF/cap/yr]": {"row": 2, "label": "Owner Subsidies"},
        "ECM Subsidies<br>[CHF/cap/yr]": {"row": 3, "label": "ECM Subsidies"},
    }

    # Row labels for left side
    row_labels = [
        "Total Subsidies [CHF/cap/yr]",
        "Owner Subsidies [CHF/cap/yr]",
        "ECM Subsidies [CHF/cap/yr]"
    ]

    # Create subplot layout with panel labels
    subplot_titles = [f"{panel_labels[i]} {urban_typologies[i]}" for i in range(4)] + [""] * 8
    fig = make_subplots(
        rows=3,
        cols=4,
        shared_xaxes=True,
        shared_yaxes=True,
        horizontal_spacing=FIGURE_CONFIG["horizontal_spacing"],
        vertical_spacing=FIGURE_CONFIG["vertical_spacing"],
        subplot_titles=subplot_titles,
    )

    # Generate heatmaps
    for metric, metric_info in metrics_to_plot.items():
        row = metric_info["row"]
        colorscale = COLOR_SCALES[metric]
        zmin = df_params[metric].min()
        zmax = df_params[metric].max()

        for col, typology in enumerate(urban_typologies, start=1):
            # Filter data for this typology
            df_group = df_params[df_params["Group"] == typology]
            x = df_group["Interest Rate"].values * 100  # Convert to percentage
            y = df_group["Tenants Affordability"].values
            z = df_group[metric].values

            # Calculate sample size for this panel
            n_samples = len(df_group)

            # Create interpolated grid
            xi, yi, zi_interp = create_interpolated_grid(x, y, z)

            # Add heatmap trace
            fig.add_trace(
                go.Heatmap(
                    z=zi_interp,
                    x=xi,
                    y=yi,
                    zmin=zmin,
                    zmax=zmax,
                    colorscale=colorscale,
                    zsmooth='best',
                    showscale=(col == 4),  # Only show colorbar on rightmost column
                    colorbar=dict(
                        title=dict(
                            text=row_labels[row - 1],
                            font=dict(size=FIGURE_CONFIG["colorbar_font_size"])
                        ),
                        yanchor="middle",
                        y=(3 - row + 0.5) / 3,
                        len=0.28,
                        thickness=15,
                        tickfont=dict(size=FIGURE_CONFIG["tick_font_size"]),
                    ) if col == 4 else None,
                ),
                row=row,
                col=col
            )

            if FIGURE_CONFIG["show_contours"]:
                fig.add_trace(
                    go.Contour(
                        z=zi_interp,
                        x=xi,
                        y=yi,
                        contours=dict(
                            coloring='none',
                            showlabels=True,
                            labelfont=dict(size=8, color='black'),


                        ),
                        line=dict(
                            color=FIGURE_CONFIG["contour_color"],
                            width=0.5
                        ),
                        ncontours=FIGURE_CONFIG["n_contours"],
                        showscale=False,
                        hoverinfo='skip',
                        showlegend=False,
                    ),
                    row=row,
                    col=col
                )

            # Add scatter overlay to show actual data points
            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=y,
                    mode="markers",
                    marker=dict(
                        color="white",
                        size=5,
                        symbol="circle",
                        line=dict(color="black", width=1)
                    ),
                    showlegend=False,
                    hovertemplate=(
                        f"<b>{typology}</b><br>"
                        f"Interest Rate: %{{x:.2f}}%<br>"
                        f"Affordability: %{{y:.3f}}<br>"
                        f"{metric_info['label']}: %{{text:.2f}}<br>"
                        f"<i>n = {n_samples}</i>"
                        f"<extra></extra>"
                    ),
                    text=z
                ),
                row=row,
                col=col
            )

    # Configure all axes with scientific styling
    fig.update_xaxes(
        showgrid=FIGURE_CONFIG["show_grid"],
        gridcolor=FIGURE_CONFIG["gridcolor"],
        gridwidth=0.5,
        zeroline=False,
        tickfont=dict(
            size=FIGURE_CONFIG["tick_font_size"],
            family=FIGURE_CONFIG["font_family"]
        ),
        title_font=dict(
            size=FIGURE_CONFIG["axis_font_size"],
            family=FIGURE_CONFIG["font_family"]
        ),
    )

    fig.update_yaxes(
        showgrid=FIGURE_CONFIG["show_grid"],
        gridcolor=FIGURE_CONFIG["gridcolor"],
        gridwidth=0.5,
        zeroline=False,
        tickfont=dict(
            size=FIGURE_CONFIG["tick_font_size"],
            family=FIGURE_CONFIG["font_family"]
        ),
        title_font=dict(
            size=FIGURE_CONFIG["axis_font_size"],
            family=FIGURE_CONFIG["font_family"]
        ),
    )

    # Add axis labels (centered across columns for x-axis, centered across rows for y-axis)
    fig.add_annotation(
        text="Interest Rate [%]",
        xref="paper",
        yref="paper",
        x=0.5,
        y=-0.05,
        showarrow=False,
        font=dict(
            size=FIGURE_CONFIG["font_size"],
            family=FIGURE_CONFIG["font_family"]
        ),
        xanchor="center",
    )

    fig.add_annotation(
        text="Tenant Affordability Coefficient",
        xref="paper",
        yref="paper",
        x=-0.05,
        y=0.5,
        showarrow=False,
        font=dict(
            size=FIGURE_CONFIG["font_size"],
            family=FIGURE_CONFIG["font_family"]
        ),
        textangle=-90,
        xanchor="center",
        yanchor="middle",
    )

    # Update subplot title fonts
    for annotation in fig['layout']['annotations'][:4]:  # Only first 4 annotations (subplot titles)
        annotation['font'] = dict(
            size=FIGURE_CONFIG["title_font_size"],
            family=FIGURE_CONFIG["font_family"]
        )

    # Update global layout with scientific styling
    fig.update_layout(
        height=FIGURE_CONFIG["height"],
        width=FIGURE_CONFIG["width"],
        template=FIGURE_CONFIG["template"],
        margin=dict(t=80, b=80, l=100, r=120),
        font=dict(family=FIGURE_CONFIG["font_family"]),
        plot_bgcolor='white',
        paper_bgcolor='white',
    )

    return fig


def save_figure(fig: go.Figure, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)

    html_path = os.path.join(output_dir, OUTPUT_FILES["html"])
    fig.write_html(html_path)
    print(f"Saved interactive HTML: {html_path}")

    pdf_path = os.path.join(output_dir, OUTPUT_FILES["pdf"])
    fig.write_image(pdf_path)
    print(f"Saved PDF figure: {pdf_path}")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """
    Main execution function.
    """
    df_params = process_all_files(DATA_PATH)
    fig = create_sensitivity_heatmap(df_params)
    fig.show()
    save_figure(fig, OUTPUT_DIR)



if __name__ == "__main__":
    main()
