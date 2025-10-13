#%%
import pandas as pd
import plotly.graph_objs as go

import plotly.io as pio
pio.kaleido.scope.mathjax = None

#%%

# Choose district type: 'GVA' or 'el'
# This will load data from /results/{district_type}_district/plot_actor/
district_type = 'GVA'  # 'GVA' or 'el'

path = f'../results/'
path_layout = 'layout/'
#%%
def plot_portfolios(df_results, df_layout, annotation_size=10):

    group_gaps = 3  # Number of empty 'gap' bars between groups

    # Calculate x_vals with gaps
    x_vals = []
    x_group_pos = []
    bar_to_x = {}
    i = 0
    for gi, g in enumerate(groups):
        group_start = i
        for b in bars:
            label = f'{g}_{b}'
            x_vals.append(label)
            bar_to_x[(g, b)] = i
            i += 1
        x_group_pos.append(group_start + (len(bars) / 2 -1)/2)
        if gi < len(groups)-1:
            for gap_id in range(group_gaps):
                x_vals.append(f'gap_{gi}_{gap_id}')
                i += 1

    # --- Prepare bar stacks with gap handling ---
    fig = go.Figure()

    for bar in bars:
        stacks = df_layout[df_layout['Bar'] == bar]['Stack'].tolist()
        for stack in stacks:
            ys = []
            for g in groups:
                v = df_results.query('Group == @g and Bar == @bar and Stack == @stack')['Value']
                ys.append(v.values[0] if not v.empty else 0)
            # Expand ys with zeros in the gap locations
            ys_with_gap = []
            for gi in range(len(groups)):
                # bars for group
                for bi in range(len(bars)):
                    if bars[bi] == bar:
                        ys_with_gap.append(ys[gi])
                    else:
                        ys_with_gap.append(0)
                # gap
                if gi < len(groups)-1:
                    ys_with_gap.extend([0]*group_gaps)
            # Color, label, legendgroup for grouped legend
            color = df_layout[(df_layout['Stack'] == stack) & (df_layout['Bar'] == bar)]['Color'].iloc[0]
            label = df_layout[(df_layout['Stack'] == stack) & (df_layout['Bar'] == bar)]['Label'].iloc[0]
            legendgroup = bar
            showlegend = (stack == stacks[0])  # Show bar group label only once in legend
            # Display bar name in the legend title, stack below it
            fig.add_bar(
                x=x_vals,
                y=ys_with_gap,
                width = 0.9,
                marker=(
                    dict(
                        color="white",
                        pattern=dict(
                            shape="x",
                            fgcolor=color,
                            size=8,
                            solidity=0.3
                        )
                    ) if stack == "Potential savings" else
                    dict(color=color)
                ),
                name=label,
                legendgroup=bar,
                legendgrouptitle_text=bar,
                showlegend=True if bar != "Subsidies" else False,
                hovertemplate=f"{bar} - {label}: %{{y}}"
            )

    for g in groups:
        for b in bars:
            df_bar = df_results[(df_results['Group'] == g) & (df_results['Bar'] == b) & (df_results['Stack'] != "Potential savings")]
            v_sum = df_bar['Value'].sum() # ECM: always annotate at y=0
            x_idx = bar_to_x[(g, b)]
            annotation_text = f"{b}<br>{v_sum:.1f}"

            # Normal: top of positive stack, bottom of negative stack
            positive_sum, negative_sum = 0, 0
            max_top, min_bottom = 0, 0
            for v in df_bar['Value']:
                if v >= 0:
                    positive_sum += v
                    max_top = positive_sum
                else:
                    negative_sum += v
                    min_bottom = negative_sum

            if v_sum >= 0:
                y_annot = max_top + 10
                valign = "bottom"
            else:
                y_annot = min_bottom - 10
                valign = "top"

            fig.add_annotation(
                x=x_vals[x_idx] if b != "Tenants" else str(g + "_Landlords"),
                y=y_annot,
                text=annotation_text,
                showarrow=False,
                font=dict(size=annotation_size, color='black'),
                bgcolor='white',
                bordercolor='black',
                borderwidth=1,
                borderpad=3,
                yanchor=valign
            )

    fig.update_layout(
        barmode='relative',
        xaxis=dict(
            tickmode='array',
            tickvals=[x_vals[int(pos) + 2] for pos in x_group_pos],
            ticktext=groups,
            categoryorder="array",
            categoryarray=x_vals,
        ),
        yaxis=dict(title="Costs [CHF/cap/yr]"),
        legend=dict(
            orientation="h",  # horizontal layout
            yanchor="bottom",
            y=-0.5,  # move legend below the figure (adjust as needed)
            xanchor="center",
            x=0.5,  # center horizontally
            traceorder="grouped",
            title=None,
            itemwidth=45,  # width of each legend item
            itemsizing="constant",
            bgcolor="rgba(0,0,0,0)",  # transparent background
            borderwidth=0,
            valign="middle",
            tracegroupgap=2,
        ),
        bargap=0.1,
    )

    return fig
#%%
groups = ['Urban', 'Low-Rise', 'High-Rise', 'Countryside']
bars = ['Tenants', 'Landlords', 'ECM', 'DSO', 'Subsidies']

df_layout = pd.read_csv(path_layout + 'actor_layout.csv')
df_results = pd.DataFrame(
    [(group, bar, row.Stack)
     for group in groups
     for bar in bars
     for _, row in df_layout[df_layout['Bar'] == bar].iterrows()],
    columns=['Group', 'Bar', 'Stack']
)
df_results = df_results.merge(df_layout, how='left', on=['Bar', 'Stack'])
df_results['Value'] = 0.0  # To be filled in by your assignment loop

#%%
results_urban_ac = pd.read_pickle(path + f'9c_Urban_{district_type}_Actors.pickle')
results_lowrise_ac = pd.read_pickle(path + f'9c_Low-rise_{district_type}_Actors.pickle')
results_highrise_ac = pd.read_pickle(path + f'9c_High-rise_{district_type}_Actors.pickle')
results_countryside_ac = pd.read_pickle(path + f'9c_Countryside_{district_type}_Actors.pickle')

results_ac = {
    "Urban": results_urban_ac,
    "Low-Rise": results_lowrise_ac,
    "High-Rise": results_highrise_ac,
    "Countryside": results_countryside_ac,
}
#%%
# Get ERA values from data
ERA = {}
for group in groups:
    ERA[group] = results_ac[group]['actors'][0]["df_Buildings"].ERA.sum()

for group in groups:
    # pull out the Network line of df_Performance
    era = ERA[group]

    net_perf = results_ac[group]['actors'][0]['df_Performance'].loc['Network'] / era * 46
    
    # get the reinforcement cost (making sure we use iloc[0])
    #reinf = results_ac[group]['actors'][0]['df_Grid'] \
    #    .xs(('Network','Electricity'), level=[0,1])['ReinforcementCost'].iloc[0]
    reinf = results_ac[group]['actors'][0]['df_Performance']['DSO_reinforce']['Network']
    reinforcement = max(reinf, 0)/ era * 46

    for bar in ['Tenants', 'Landlords', 'ECM', 'DSO', 'Subsidies']:
        # dynamically grab all stacks for this group/bar
        stacks = df_results.loc[
            (df_results['Group'] == group) & (df_results['Bar'] == bar),
            'Stack'
        ].unique()

        for stack in stacks:
            mask = (
                (df_results['Group'] == group) &
                (df_results['Bar']   == bar) &
                (df_results['Stack'] == stack)
            )

            # compute the right value for each (bar, stack) pair
            if bar == 'Tenants':
                if stack == 'Electricity from Landlords':
                    val = net_perf['C_op_renters_to_owners']
                elif stack == 'Electricity from ECM':
                    val = net_perf['C_op_renters_to_ECM'] #- net_perf['Cost_supply_district_mobility']
                elif stack == 'Private mobility from ECM':
                    val = net_perf['C_renters_to_ECM_mobility']
                elif stack == 'Subsidies to Tenants':
                    val = - net_perf['renter_subsidies']
                elif stack == 'Potential savings':
                    # TODO: Update these values for new districts
                    if group == 'Urban':
                        val = 0  # Update with correct value
                    elif group == 'Low-Rise':
                        val = 0  # Update with correct value
                    elif group == 'High-Rise':
                        val = 0  # Update with correct value
                    elif group == 'Countryside':
                        val = 0  # Update with correct value
                    else:
                        val = 0
                else:
                    continue

            elif bar == 'Landlords':
                if stack == 'Building equipment':
                    val = net_perf['owner_inv']
                elif stack == 'Electricity to Tenants':
                    val = - net_perf['C_op_renters_to_owners']
                elif stack == 'Electricity to ECM':
                    val = - net_perf['C_op_ECM_to_owners']
                elif stack == 'Subsidies to Landlords':
                    val = - net_perf['owner_subsidies']
                else:
                    continue

            elif bar == 'ECM':
                if stack == 'District equipment':
                    val = 146.8/2633 * (net_perf['Costs_inv'] - net_perf['owner_inv'])
                elif stack == 'Electric vehicles':
                    val = (1-146.8/2633) * (net_perf['Costs_inv'] - net_perf['owner_inv'])
                elif stack == 'Electricity to DSO':
                    val = - net_perf['C_op_DSO_to_ECM']
                elif stack == 'Electricity from DSO':
                    val = net_perf['C_op_ECM_to_DSO']
                elif stack == 'Electricity from Landlords':
                    val = net_perf['C_op_ECM_to_owners']
                elif stack == 'Electricity to Tenants':
                    val = - net_perf['C_op_renters_to_ECM']
                elif stack == 'Mobility to Tenants':
                    val = - net_perf['C_renters_to_ECM_mobility']
                elif stack == 'Subsidies to ECM':
                    val = - net_perf['ECM_subsidies']
                else:
                    continue

            elif bar == 'DSO':
                if stack == 'Electricity from ECM':
                    val = net_perf['C_op_DSO_to_ECM']
                elif stack == 'Electricity import':
                    val = net_perf['C_op_DSO_to_extern']
                elif stack == 'Electricity to ECM':
                    val = - net_perf['C_op_ECM_to_DSO']
                elif stack == 'Electricity export':
                    val = - net_perf['C_op_extern_to_DSO']
                elif stack == 'Grid reinforcement':
                    val = reinforcement
                elif stack == 'Subsidies to DSO':
                    val = 0
                else:
                    continue

            elif bar == 'Subsidies':
                if stack == 'Subsidies to Tenants':
                    val = net_perf['renter_subsidies']
                elif stack == 'Subsidies to Landlords':
                    val = net_perf['owner_subsidies']
                elif stack == 'Subsidies to ECM':
                    val = net_perf['ECM_subsidies']
                elif stack == 'Subsidies to DSO':
                    val = 0
                else:
                    continue

            # finally set the DataFrame
            df_results.loc[mask, 'Value'] = round(val, 2)
#%%
fig = plot_portfolios(df_results, df_layout, annotation_size=18)

fig.add_hline(
    y=0,
    line=dict(color="grey", width=2)
)

fig.add_annotation(
    x=-0.05, y=1.01,
    xref="paper", yref="paper",
    text="Expenses",
    showarrow=False,
    font=dict(size=22, color="black"),
    bgcolor="mistyrose",  # pale red
    bordercolor="rgba(220,20,60,0.3)",  # Optional: red border
    borderpad=4,
    align="center"
)

fig.add_annotation(
    x=-0.05, y=-0.01,
    xref="paper", yref="paper",
    text="Profits",
    showarrow=False,
    font=dict(size=22, color="black"),
    bgcolor="honeydew",  # pale green
    bordercolor="rgba(50,205,50,0.3)",  # Optional: green border
    borderpad=4,
    align="center"
)

fig.update_layout(
    template='plotly_white',
    font=dict(
        family="Arial, sans-serif",
        size=20,
        color="#000000"
    ),
    width=1400,
    height=1000,
    margin=dict(l=10, r=10, t=20, b=40),
    plot_bgcolor='white',
    paper_bgcolor='white'
)

#%%
#fig.show()
print("Generating outputs...")
try:
    fig.write_image(f"plots/plot_actors_{district_type}.pdf",
                    width=1400,
                    height=1000,
                    scale=2)
    print("PDF saved successfully!")
except Exception as e:
    print(f"Warning: Could not save PDF: {e}")
fig.write_html(f"plots/plot_actors_{district_type}.html")
print("HTML plot saved successfully!")

#%%
