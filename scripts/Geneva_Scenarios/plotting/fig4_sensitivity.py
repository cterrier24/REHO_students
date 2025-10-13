#%%
import pandas as pd
import plotly.graph_objects as go
from jedi.inference.base_value import iterator_to_value_set
from plotly.subplots import make_subplots
import os

import plotly.io as pio
pio.kaleido.scope.mathjax = None
#%%
root = '/Users/ziqian/Desktop/MA/geneva_paper_plot'

path = root +'/results/plot4/'

explanatories = ["Tenants Affordability", "Landlords Profitability"]
groups     = ["Center", "Villa", "Rural"]

R_vals     = [0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2]
O_vals     = [0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2]
i_vals     = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1]

era_map      = {"Center": 33438, "Villa": 13713, "Rural": 14178}
responses    = ["Subsidies", "SS", "SC", "GWP", "PV"]

def make_filename(group: str, sens: float, var: str) -> str:
    if var == 'Renter':
        tag = f"9c_{group}_Renter{sens}_Actors_SCITAS.pickle"
    elif var == 'Owner':
        tag = f"9c_{group}_Owner{sens - 0.5:.1f}_Actors_SCITAS.pickle"
    return os.path.join(path, tag)

rent_maps = {
    grp: {
        r: pd.read_pickle(make_filename(grp, r, 'Renter'))
        for r in R_vals
    }
    for grp in groups
}


#owner_maps = {
#    grp: {
#        o: pd.read_pickle(make_filename(grp, o, 'Owner'))
#        for o in O_vals
#    }
#    for grp in groups
#}

interest_rate_maps = {
    grp: {
        i: pd.read_pickle(f"{path}9c_{grp}_interest{i:.2f}_Actors_SCITAS.pickle")  # Adjust this wildcard to match
        for i in i_vals
    }
    for grp in groups
}

#%%
# Build the renters DataFrame from rent_maps
rows = []
for group, rmap in rent_maps.items():
    era = era_map[group]
    for R, res in rmap.items():
        perf = res["actors"][0]["df_Performance"]
        kpi  = res["actors"][0]["df_KPIs"]
        unit = res["actors"][0]["df_Unit"]["Units_Mult"]

        for resp in responses:
            if resp == "Subsidies":
                val = (
                    perf["renter_subsidies"]["Network"]
                  + perf["owner_subsidies"]["Network"]
                  + perf["ECM_subsidies"]["Network"]
                ) / era * 46
            elif resp == "GWP":
                val = perf["GWP_constr"]["Network"] / era * 46
            elif resp == "PV":
                val = unit[unit.index.str.contains("PV")].sum()
            else:
                val = kpi[resp]["Network"]

            rows.append({
                "Group":                group,
                "Tenants Affordability": R,
                "Response":             resp,
                "Value":                val
            })

df = pd.DataFrame(rows)

#Standardize renters → df_std
baseline = (
    df[df["Tenants Affordability"] == 1.0]
      .set_index(["Group","Response"])["Value"]
      .rename("Baseline")
)

df_std = (
    df
    .merge(baseline, left_on=["Group","Response"], right_index=True)
    .assign(Value_std=lambda d: d["Value"]/d["Baseline"])
    .drop(columns="Baseline")
)

df_std["ExplanatoryVal"]   = df_std["Tenants Affordability"]
#%%
#Build the owners DataFrame from owner_maps
interest_explan   = "Interest Rate"
rows_i = []

for group, omap in interest_rate_maps.items():
    era = era_map[group]
    for R, res in omap.items():
        perf = res["actors"][0]["df_Performance"]
        kpi  = res["actors"][0]["df_KPIs"]
        unit = res["actors"][0]["df_Unit"]["Units_Mult"]

        for resp in responses:
            if resp == "Subsidies":
                val = (
                    perf["renter_subsidies"]["Network"]
                  + perf["owner_subsidies"]["Network"]
                  + perf["ECM_subsidies"]["Network"]
                ) / era * 46
            elif resp == "GWP":
                val = perf["GWP_constr"]["Network"] / era * 46
            elif resp == "PV":
                val = unit[unit.index.str.contains("PV")].sum()
            else:
                val = kpi[resp]["Network"]

            rows_i.append({
                "Group":             group,
                interest_explan:        R,
                "Response":          resp,
                "Value":             val
            })

df_i = pd.DataFrame(rows_i)

baseline_i = (
    df_i[df_i[interest_explan] == 0.02]
       .set_index(["Group","Response"])["Value"]
       .rename("Baseline")
)

df_i_std = (
    df_i
    .merge(baseline_i, left_on=["Group","Response"], right_index=True)
    .assign(Value_std=lambda d: d["Value"]/d["Baseline"])
    .drop(columns="Baseline")
)

df_i_std["ExplanatoryVal"] = df_i_std["Interest Rate"]
#%%
colors = {"Center":"#c78c7f","Villa":"#a39460","Rural":"#7ea360"}
markers = {"Center":"circle","Villa":"square","Rural":"star-triangle-up"}
#%%
# Create a 3×2 grid (3 responses × 2 explanatories)
resp_list = ["Subsidies", "GWP", "PV"]

fig = make_subplots(
    rows=3, cols=2,
    shared_xaxes=True,    # share X across columns
    shared_yaxes=True,    # share Y across rows
    horizontal_spacing=0.05,
    vertical_spacing=0.05,
    subplot_titles=[""]*6
)

for i, resp in enumerate(resp_list, start=1):
    # OWNER (col=1)
    df_i = df_i_std[df_i_std["Response"] == resp]
    for grp in groups:
        dff = df_i[df_i["Group"] == grp]
        fig.add_trace(
            go.Scatter(
                x=dff["ExplanatoryVal"],
                y=dff["Value_std"],
                mode="lines+markers",
                name=grp,
                marker=dict(
                    color=colors[grp],
                    symbol=markers[grp],
                    line=dict(color=colors[grp], width=3)
                ),
                showlegend=(i==1)
            ),
            row=i, col=1
        )

    # RENTER (col=2)
    df_r = df_std[df_std["Response"] == resp]
    for grp in groups:
        dff = df_r[df_r["Group"] == grp]
        fig.add_trace(
            go.Scatter(
                x=dff["ExplanatoryVal"],
                y=dff["Value_std"],
                mode="lines+markers",
                name=grp,
                marker=dict(
                    color=colors[grp],
                    symbol=markers[grp],
                    line=dict(color=colors[grp], width=3)
                ),
                showlegend=False
            ),
            row=i, col=2
        )

fig.add_annotation(
    text="Tenants Affordability",
    x=0.5, y=1.08,
    xref="x domain", yref="paper",
    showarrow=False,
	xanchor="center",
    font=dict(size=14)
)
fig.add_annotation(
    text="Interest Rate",
    x=0.5, y=1.08,
    xref="x2 domain", yref="paper",
    showarrow=False,
	xanchor="center",
    font=dict(size=14)
)

row_labels = ["Subsidies", "GWP", "PV penetration"]
y_positions = [0.84, 0.50, 0.16]

for label, y in zip(row_labels, y_positions):
    fig.add_annotation(
        text=label,
        x=1.02, y=y,
        xref="paper", yref="paper",
        showarrow=False,
        font=dict(size=14, color="black"),
	    textangle=90,
        xanchor="left",
	    yanchor="middle"
    )


# Style the strip‐labels (subplot_titles)
for anno in fig.layout.annotations:
    anno.font.color = "grey"
    anno.font.size  = 14

#  Global axis titles
fig.add_annotation(
    text="Explanatory",
    x=0.5, y=0, xref="paper", yref="paper",
    showarrow=False, yshift=-40,
    font=dict(size=14, color="black")
)
fig.add_annotation(
    text="Response",
    x=0, y=0.5, xref="paper", yref="paper",
    showarrow=False, textangle=-90, xshift=-60,
    font=dict(size=14, color="black")
)

fig.add_shape(
    type="rect",
    xref="paper", yref="paper",
    x0=0,   x1=0.48,      # left half
    y0=0,   y1=1.08,        # full height
    fillcolor="white",  # semi‐transparent gray
    layer="below",
    line_width=0
)

# shade right colum
fig.add_shape(
    type="rect",
    xref="paper", yref="paper",
    x0=0.52, x1=1,        # right half
    y0=0,   y1=1.08,        # full height
    fillcolor="white",  # slightly darker semi‐transparent
    layer="below",
    line_width=0
)

fig.update_layout(
    legend=dict(
        orientation="h",
        x=0.5, y=-0.2,
        xanchor="center", yanchor="bottom",
	    font=dict(color="black")
    ),
    template='plotly_white',
    margin=dict(l=80, r=80, t=80, b=100),
    width=800,
    height=600,
    font=dict(size=12),
)

#%%
fig.write_image("plots/fig4_sensitivity.pdf")
#%%