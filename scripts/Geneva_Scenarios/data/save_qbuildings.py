import pandas as pd
from reho.model.actors_problem import *
from utils import remove_nan_QBuilding

qbuildings_data = {}

for i in range(11,23):
	case_study = i  # Center: 0; Villa:1 ; Rural:2
	df_case_study = pd.read_csv('scripts/examples/Geneva_Scenarios/case_study.csv')
	district_boundary = df_case_study.loc[case_study]['boundary']
	# Set building parameters
	reader = QBuildingsReader()
	reader.establish_connection('Suisse')
	neighborhood_type = df_case_study.loc[case_study]['case_study']
	# Set building parameters
	data = reader.read_db(district_boundary=district_boundary,
	                                 district_id=int(df_case_study.loc[case_study]['id_neighborhood']))
	qbuildings_data[neighborhood_type] = remove_nan_QBuilding(data)
	print(f"✅ QBuilding data {neighborhood_type} imported successfully.")

pd.to_pickle(qbuildings_data, 'scripts/examples/Geneva_Scenarios/qbuildings_data_CH.pickle')
