######################################################################################################################################
#### Plot the different graph (Sankey, GWP, cost) once the results have already been saved. It imports the add_consumption()      ####
#### function from write_PT_results.py to try to account for replacement costs, not considered yet in this version of REHO.       ####
#### GWP and costs can be plotted individually, or all together under the form of a Pareto plot (last line commented)             ####
######################################################################################################################################



from reho.model.reho import *
from reho.plotting import plotting
from reho.model.postprocessing.write_PT_results import *
from scripts.examples.mobility_sector_PT_7a import dict_param


def sankey(pickle):
    #results = pickle['totex'][0]
    #plotting.plot_sankey(pickle['totex'][0], label='EN_long', color='ColorPastel', title=f"Sankey diagram 3230 - 2050 no PVHP fix").show()
    plotting.plot_sankey(pickle['totex'][0], label='EN_long', color='ColorPastel', title=f"Sankey diagram 3230 - 2050 fix").show()

def economic(pickle):
    plotting.plot_performance(pickle, plot='costs', indexed_on='Pareto_ID', label='EN_long', title='Economical performance 3230 - 2050', per_pers=True, parameters=dict_param, year=2050, transformer=3230).show()
    #plotting.plot_performance(pickle, plot='costs', indexed_on='Pareto_ID', label='EN_long', title='Economical performance 3230 - 2024 noPVHP', per_pers=True, parameters=dict_param, year=2024, transformer=3230).show()

def gwp(pickle):
    plotting.plot_performance(pickle, plot='gwp', indexed_on='Pareto_ID', label='EN_long', title='GWP 3230 - 2024', per_pers=True, parameters=dict_param, year=2024, transformer=3230).show()
    #plotting.plot_performance(pickle, plot='gwp', indexed_on='Pareto_ID', label='EN_long', title='GWP 3230 - 2024 noPVHP', per_pers=True, parameters=dict_param, year=2024, transformer=3230).show()


if __name__ == '__main__':
    file24 = pd.read_pickle("../examples/results/3230/fix/7a_3230_2024_fix.pickle")
    file24_no = pd.read_pickle("../examples/results/3230/fix/7a_3230_2024_no_PVHP_fix.pickle")
    file30 = pd.read_pickle("../examples/results/3230/fix/7a_3230_2030_fix.pickle")
    file30_no = pd.read_pickle("../examples/results/3230/fix/7a_3230_2030_no_PVHP_fix.pickle")
    file50 = pd.read_pickle("../examples/results/3230/fix/7a_3230_2050_fix.pickle")
    file50_no = pd.read_pickle("../examples/results/3230/fix/7a_3230_2050_no_PVHP_fix.pickle")
    #file50fix = pd.read_pickle("../examples/results/7a_3230_2050_fix.pickle")
    #file = pd.read_pickle("../examples/results/3230/baseline/7o_3230.pickle")
    #file = pd.read_pickle("../examples/results/7a_3230_2050_relax.pickle")
    add_consumption(file24,outside=True)
    add_consumption(file24_no,outside=True)
    add_consumption(file30,outside=True)
    add_consumption(file30_no,outside=True)
    add_consumption(file50,outside=True)
    add_consumption(file50_no,outside=True)
    #add_consumption(file50fix,outside=True)
    #add_consumption(file,outside=True)
    sankey(file50)
    #economic(file50fix)
    #economic(file_no)
    #gwp(file)
    #gwp(file_no)
    #pareto = pd.read_pickle("../examples/results/7a_3230_2024_Pareto.pickle")
    pareto = {'pareto': {'baseline-24': file24_no['totex'][0], 'baseline-30': file30_no['totex'][0], 'baseline-50': file50_no['totex'][0], 'PV/HP-24': file24['totex'][0], 'PV/HP-30': file30['totex'][0], 'PV/HP-50': file50['totex'][0]}}
    #plotting.plot_performance(pareto, plot='gwp', indexed_on='Pareto_ID', label='EN_long', title='GWP comparison 3230 - fixed', per_pers=True, parameters=dict_param, transformer=3230, single=False).show()

    2024
    2030
    2050

    3216
    3217
    3230