#%%
import plotly.io as pio
pio.kaleido.scope.mathjax = None

import plotly.graph_objects as go
import numpy as np
import pandas as pd
import re
import kaleido
#%%

#%%
def prepare_dfs(df_Economics, indexed_on='Scn_ID', neg=False, include_avoided=False, additional_data=None, scaling_factor=1, ERA=None, per_cap=False):
    """
    This function prepares the dataframes that will be needed for the plot_performance and plot_expenses
    """

    if additional_data is None:
        additional_data = {}
    df_Economics = df_Economics.xs('Network', level='Hub', axis=0)
    df_Economics = df_Economics.groupby(level=indexed_on, sort=False).sum() * scaling_factor
    indexes = df_Economics.index.tolist()

    data_capacities = df_Economics.xs('investment', level='Category', axis=1).transpose()
    data_capacities.index.names = ['Unit']

    if 'isolation' in additional_data:
        data_capacities.loc['Isolation', :] = additional_data['isolation']
    if 'reinforcement' in additional_data:
        data_capacities.loc['Reinforcement', :] = additional_data['reinforcement']


    data_capacities = data_capacities.reset_index().merge(layout, left_on="Unit", right_on='Name').set_index("Unit").fillna(0)

    data_resources = df_Economics.xs('operation', level='Category', axis=1).transpose()
    indices = data_resources.index.get_level_values(0)
    new_indices = []
    [new_indices.append(tuple(idx.split("_", 1))) for idx in indices]

    energy_layers = ['Electricity', 'Heat', 'Oil', 'NaturalGas', 'Gasoline', 'Wood', 'Hydrogen', 'Biomethane', 'Data', 'Mobility']

    for i, tup in enumerate(new_indices):
        for energy in energy_layers:
            if tup == ('costs', energy):
                new_indices[i] = ('costs', f'{energy}_import')
                break
            elif tup == ('revenues', energy):
                new_indices[i] = ('revenues', f'{energy}_export')
                break

    data_resources.index = pd.MultiIndex.from_tuples(new_indices, names=['type', 'Layer'])

    if include_avoided is not False:

        data_resources.loc[('costs', 'Electricity_import'), :] = data_resources.loc[('costs', 'Electricity_import'), :] + data_resources.loc[('avoided', 'PV_SC'), :]
        if include_avoided is True:
            pass
        elif 'sc_premium' in include_avoided:
            retail_price = include_avoided['sc_premium'][0]
            feedin_price = include_avoided['sc_premium'][1]

            data_resources.loc[('revenues', 'solar_value'), :] = data_resources.loc[('revenues', 'Electricity_export')] + feedin_price * data_resources.loc[
                ('avoided', 'PV_SC')] / retail_price

            data_resources.loc[('avoided', 'sc_premium'), :] = data_resources.loc[('avoided', 'PV_SC')] * (retail_price - feedin_price) / retail_price

            data_resources = data_resources.drop("PV_SC", level='Layer')
            data_resources = data_resources.drop("Electricity_export", level='Layer')
    else:
        data_resources.loc[('avoided', 'PV_SC'), :] = 0

    data_resources = data_resources.drop("PV", level='Layer')

    if 'mobility' in additional_data:
        data_resources.loc[('costs', 'Gasoline_import'), :] = additional_data['mobility']

    if 'public_transportation' in additional_data:
        data_resources.loc[('costs', 'PublicTransport'), :] = additional_data['public_transportation']

    if 'ict' in additional_data:
        data_resources.loc[('costs', 'Data_export'), :] = additional_data['ict']
    if additional_data.get('no_ict_profit', False):
        data_resources.loc[('revenues', 'Data_export'), :] = 0

    if neg:
        indices = data_resources.index.get_level_values(0)
        neg_indices = indices.str.contains('avoided')
        neg_indices = neg_indices + indices.str.contains('revenues')
        data_resources.loc[neg_indices] = - data_resources.loc[neg_indices]
    data_resources = data_resources.reset_index().merge(layout, left_on='Layer', right_on='Name').set_index(['type', 'Layer'])
    
    if ERA is not None:
        # Normalize by ERA
        for i, era in ERA.items():
            if era != 0:
                data_capacities[i] /= era
                data_resources[i] /= era

        # Multiply per capita if requested
        if per_cap:
            for i, era in ERA.items():
                data_capacities[i] *= 46
                data_resources[i] *= 46
        
    return indexes, data_capacities, data_resources

def custom_round(value, decimal):
    if decimal == 0:
        rounded_value = int(round(value))
    elif decimal == 1:
        rounded_value = round(value, 1)
    else:
        raise ValueError("decimal argument must be 0 or 1")
    return rounded_value

def aggregate_df_Economics(df):
    new_tuples = []
    for tup in df.columns:
        *prefix, leaf = tup
        leaf_stripped = re.sub(r'_\d+$', '', leaf)
        new_tuples.append((*prefix, leaf_stripped))

    df.columns = pd.MultiIndex.from_tuples(new_tuples, names=df.columns.names)

    return df.groupby(axis=1, level=list(range(df.columns.nlevels))).sum()

def aggregate_df_Annuals(df):
    mi = df.index

    new_hub = (
        mi.get_level_values('Hub')
        .str.replace(r'_\d+', '', regex=True)
    )

    df.index = pd.MultiIndex.from_arrays(
        [mi.get_level_values('Layer'), new_hub],
        names=mi.names
    )
    return df
def get_ghg_reduction(result1, result2, ERA):
    GWP_red = []

    for key in ['Urban', 'Low-Rise', 'High-Rise', 'Countryside']:
        df1 = result1[key][0]['df_Performance']
        df2 = result2[key][0]['df_Performance']

        GWP_1 = (df1['GWP_constr']['Network'] + df1['GWP_op']['Network'])/ERA[key]*46 / 1000
        GWP_2 = (df2['GWP_constr']['Network'] + df2['GWP_op']['Network'])/ERA[key]*46 / 1000
        
        print(GWP_1, GWP_2)

        GWP_red.append(GWP_1 - GWP_2)

    return GWP_red

#%%
district_type = 'El' #'el'
layout = pd.read_csv('layout/totex_layout.csv', index_col='Name').dropna(how='all')

results_urban = pd.read_pickle(f'../results/9a_Urban_{district_type}_TOTEX_wo_El.pickle')
results_lowrise = pd.read_pickle(f'../results/9a_Low-rise_{district_type}_TOTEX_wo_El.pickle')
results_highrise = pd.read_pickle(f'../results/9a_High-rise_{district_type}_TOTEX_wo_El.pickle')
results_countryside = pd.read_pickle(f'../results/9a_Countryside_{district_type}_TOTEX_wo_El.pickle')


results_urban['Urban'] = results_urban.pop('actors')
results_lowrise['Low-Rise'] = results_lowrise.pop('actors')
results_highrise['High-Rise'] = results_highrise.pop('actors')
results_countryside['Countryside'] = results_countryside.pop('actors')

#%%
results = {**results_urban, **results_lowrise ,**results_highrise, **results_countryside}
#%%
for scn in results:
    for id in results[scn]:
        results[scn][id]["df_Economics"] = aggregate_df_Economics(results[scn][id]["df_Economics"])
        results[scn][id]["df_Annuals"] = aggregate_df_Annuals(results[scn][id]["df_Annuals"])
        
sc = list(results.keys())
t = {(Scn_ID, Pareto_ID): results[Scn_ID][Pareto_ID]['df_Economics']
     for Scn_ID in results.keys()
     for Pareto_ID in results[Scn_ID].keys()}

df_Economics = pd.concat(t.values(), keys=t.keys(), names=['Scn_ID', 'Pareto_ID'], axis=0)
df_costs = df_Economics.xs('costs', level='Perf_type')

change_data = pd.DataFrame()
change_data.index = ['x_axis_1', 'x_axis_2', 'y_axis', 'keyword', 'total', 'unites', 'scc_legend']
change_data['EN'] = ['CAPEX', 'OPEX', 'Costs [CHF/cap/yr]', 'Costs', 'TOTEX', ' CHF','']
decimal = 0
label = 'EN_long'
lang = re.split('_', label)[0]
#%%
# Add additional data
dict_Isolation = {
    (scn_id, pareto_id): pd.DataFrame({
        'Costs_ins': (
            pareto_data.get('df_Performance', pd.DataFrame())
            .get('Costs_ins', pd.Series([0]))  
            .drop(0, errors='ignore')    
        )
    })
    for scn_id, pareto_dict in results.items()
    for pareto_id, pareto_data in pareto_dict.items()
}
list_isolation = [
    df.at['Network', 'Costs_ins'] if 'Network' in df.index else 0
    for df in dict_Isolation.values()
]

dict_Reinforce = {
    (scn_id, pareto_id): pd.DataFrame({
        'ReinforcementCost': pareto_data['df_Grid']['ReinforcementCost']['Network']

    })
    for scn_id, pareto_dict in results.items()
    for pareto_id, pareto_data in pareto_dict.items() 
}

list_Reinforce = [
    df.loc['Electricity', 'ReinforcementCost']
    for df in dict_Reinforce.values()
]

list_public_transportation = [
    pareto_dict[0]['df_Annuals']['Supply_MWh']['Mobility']['Network'] * 3000
    for scn_id, pareto_dict in results.items()
]

ERA = pd.Series(dtype=float)
for i in results:
    ERA[i] = results[i][0]["df_Buildings"].ERA.sum()

additional_data = {'isolation': list_isolation, 'reinforcement': list_Reinforce,
                   'public_transportation': list_public_transportation}
indexes, data_capacities, data_resources = prepare_dfs(df_costs, 'Scn_ID', neg=True,
                                                       additional_data = additional_data, ERA=ERA, per_cap=True)

# Remove electric bikes from the plot
if 'ElectricBike_district' in data_capacities.index:
    data_capacities = data_capacities.drop('ElectricBike_district')
#data_resources = data_resources.drop('Mobility', level='Layer')

#%%
districts = ['Urban','Low-Rise','High-Rise','Countryside']
df_costs = data_resources.xs('costs', level='type').loc[:, districts].astype(float)

min_factors = pd.Series({"Electricity_import": 0.7,
                        "Gasoline_import":    0.63,
                        "NaturalGas_import":  0.9,
                        "Mobility":           1.0
                        })

max_factors = pd.Series({"Electricity_import": 1.1,
                        "Gasoline_import":    1.1,
                        "NaturalGas_import":  1.3,
                        "Mobility":           1.0
                        })

opex_min = df_costs.mul(min_factors, axis=0).sum(axis=0)
opex_max = df_costs.mul(max_factors, axis=0).sum(axis=0)

# 3) combine into a single DataFrame
OPEX_adj = pd.DataFrame({
    'min': opex_min,
    'max': opex_max
})

# 1) extract arrays in the right order
min_vals = OPEX_adj.loc[indexes, 'min'].values
max_vals = OPEX_adj.loc[indexes, 'max'].values
opt_vals = df_costs[districts].sum().values
custom = np.stack([min_vals, max_vals], axis=1)  # shape (4,2)
custom
#%%

#%%
data_resources = data_resources.drop("avoided", level='type')

data_scc_resources = pd.DataFrame(0, columns=[indexes], index=data_resources.index)
data_scc_capacities = pd.DataFrame(0, columns=[indexes], index=data_capacities.index)
sum_resources = data_resources[indexes].sum(axis=0).reset_index(drop=True)
sum_capacities = data_capacities[indexes].sum(axis=0).reset_index(drop=True)
sum_scc_resources = data_scc_resources[indexes].sum(axis=0).reset_index(drop=True)
sum_scc_capacities = data_scc_capacities[indexes].sum(axis=0).reset_index(drop=True)
combined_resources = sum_resources + sum_scc_resources
combined_capacities = sum_capacities + sum_scc_capacities

x1 = list(range(len(indexes)))
x2 = [x + 1 / 3 for x in x1]
x3 = [x + 1 / 2 for x in x1]
x4 = [x + 4 / 12 for x in x1]
xtick = [x + 1 / 6 for x in x1]
x_ref = [x + 1/2 for x in x1]

text_capacities = [str(custom_round(cp, decimal))
                   for cp in combined_capacities]
text_resources = [str(custom_round(op, decimal))
                  for op in combined_resources]
pos_resources = data_resources[indexes][data_resources[indexes] > 0].sum(axis=0).reset_index(drop=True) + data_scc_resources[indexes][
    data_scc_resources[indexes] > 0].sum(axis=0).reset_index(drop=True)
#%%
showlegend = True
fig = go.Figure()
neg_resources = combined_resources - pos_resources
text_placeholder = 0.05 * max(max(combined_capacities - neg_resources + combined_resources),
                              max(combined_capacities + combined_resources + neg_resources),
                              max(combined_resources))
for i in range(len(indexes)):
    fig.add_annotation(x=x2[i], y=-text_placeholder,
                       text=text_resources[i],
                       font=dict(size=18, color="#000000", family="Arial, sans-serif"),
                       textangle=0, align='center', valign='top',
                       showarrow=False)
    fig.add_annotation(x=x1[i], y=-text_placeholder,
                       text=text_capacities[i],
                       font=dict(size=18, color="#000000", family="Arial, sans-serif"),
                       textangle=0, align='center', valign='top',
                       showarrow=False
                       )
    fig.add_annotation(x=xtick[i], y=max(combined_capacities[i], pos_resources[i],
                                         combined_capacities[i] + combined_resources[i]) + text_placeholder,
                       text="<b>" + str(custom_round((combined_capacities[i] + combined_resources[i]), decimal)) + "</b>",
                       font=dict(size=18, color="#000000", family="Arial, sans-serif"),
                       textangle=0, align='center', valign='top',
                       showarrow=False
                       )
for line, tech in data_capacities.iterrows():
    if tech.loc[indexes].sum() > 0:
        fig.add_trace(
            go.Bar(name=tech[label],
                   x=x1,
                   y=tech[indexes],
                   marker_color=tech["ColorPastel"],
                   width=1/6,
                   hovertemplate=f'<b>{tech[label]}</b><br>{change_data.loc["keyword", lang]}: %{{y:.{decimal}f}}{change_data.loc["unites", lang]}',
                   legendgroup='group1',
                   legendgrouptitle_text=change_data.loc['x_axis_1', lang],
                   showlegend=showlegend)
        )

        
for line, layer in data_resources.iterrows():
    if abs(layer.loc[indexes].sum()) > 0:
        fig.add_trace(go.Bar(
            name=layer[label],
            x=x2,
            y=layer[indexes],
            marker_color=layer["ColorPastel"],
            width=1/6,
            hovertemplate=(
                f"<b>{layer[label]}</b><br>"
                f"{change_data.loc['keyword', lang]}: %{{y:.{decimal}f}}"
                f"{change_data.loc['unites', lang]}"
            ),
            legendgroup='group2',
            legendgrouptitle_text=change_data.loc['x_axis_2', lang],
            showlegend=showlegend
        ))

fig.add_trace(go.Scatter(
    x=x4,
    y=opt_vals,
    mode='markers',
    marker=dict(size=3, color='#000000'),  # Slightly larger, pure black
    customdata=custom,
    error_y=dict(
        type='data',
        symmetric=False,
        array= max_vals - opt_vals,
        arrayminus= opt_vals - min_vals,
        thickness=2.5,  # Thicker for visibility
        width=18,  # Wider caps
        color='#000000'  # Pure black
    ),
    hovertemplate=(
        "<b>OPEX uncertainty</b><br>"
        "Min: %{customdata[0]:.2f}<br>"
        "Opt: %{y:.2f}<br>"
        "Max: %{customdata[1]:.2f}<extra></extra>"
    ),
    name='Uncertainty range',
    legendgroup='group2',
    legendgrouptitle_text=change_data.loc['x_axis_2', lang],
    showlegend=False,
    yaxis='y'
))

fig.add_trace(go.Scatter(
    x=[None], y=[None],
    mode='lines',
    line=dict(color='#000000', width=2.5),  # Match error bar style
    name='Uncertainty range',
    legendgroup='group2',
    legendgrouptitle_text=change_data.loc['x_axis_2', lang],
    showlegend=True
))

fig.add_trace(
    go.Bar(
        name="Fossil Reference",
        x=xtick,
        y=sum_capacities + sum_resources,
        marker_color="#737373",
        width=1 / 6,
        legendgroup='group3',
        legendgrouptitle_text='Total Costs',
        showlegend=showlegend)
)

fig.update_layout(
                  barmode="relative",
                  bargap=0,
                  template='plotly_white',
                  width=1400,  # Wider for better readability
                  height=700,  # Taller for better proportions
                  font=dict(
                      family="Arial, sans-serif",  # Professional font
                      size=18,  # Larger for publication
                      color="#000000"  # Pure black for clarity
                  ),
                  margin=dict(l=80, r=40, t=40, b=100),  # Better margins
                  xaxis=dict(
                      tickmode='array',
                      tickvals=xtick,
                      ticktext=indexes,
                      tickfont=dict(size=20, color="#000000"),  # Larger district labels
                      linecolor='#000000',  # Black axis line
                      linewidth=2,
                      mirror=False,
                      showgrid=False
                  ),
                  yaxis=dict(
                      title=dict(
                          text=change_data.loc['y_axis', lang],
                          font=dict(size=22, color="#000000"),
                          standoff=20
                      ),
                      tickfont=dict(size=18, color="#000000"),
                      linecolor='#000000',  # Black axis line
                      linewidth=2,
                      mirror=False,
                      showgrid=True,  # Grid for easier reading
                      gridcolor='#E5E5E5',  # Light grey grid
                      gridwidth=1,
                      zeroline=True,
                      zerolinecolor='#000000',
                      zerolinewidth=2
                  ),
                  legend=dict(
                      font=dict(size=16),
                      bgcolor='rgba(255,255,255,0.9)',  # Semi-transparent white background
                      bordercolor='#000000',
                      borderwidth=1,
                      x=1.02,  # Position outside plot area
                      y=1,
                      xanchor='left',
                      yanchor='top',
                      itemsizing='constant'
                  ),
                  plot_bgcolor='white',  # Pure white background
                  paper_bgcolor='white'
                  )

#%%
print("Generating outputs...")
try:
    # High-quality PDF output for publication
    fig.write_image( f"plots/plot_fossil_{district_type}.pdf",
                    width=1400, height=700, scale=2)  # Scale=2 for higher DPI
    print("PDF saved successfully!")
except Exception as e:
    print(f"Warning: Could not save PDF: {e}")
fig.write_html(f"plots/plot_fossil_{district_type}.html")
print("HTML plot saved successfully!")
