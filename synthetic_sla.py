# Request synthetic data from the DT API
# Loop through each test + location
# Record the average for test availability
# Display each test name alongside average availability for the period

import json
import csv
import numpy as np
import requests

def dynatrace_api_request(url, token, timeseries_id, relative_time='day'):
	request_url = f'{url}/api/v1/timeseries/{timeseries_id}?includeData=true&relativeTime={relative_time}'
	headers = { 
		'Accept': 'application/json', 
		'Authorization': f'Api-Token {token}'
	}

	response = requests.get(request_url, headers=headers)
	response.raise_for_status()

	return response.json()

def build_availability_dict(dt_json):
	sla_dict = {}

	try:
		data_result = dt_json['dataResult']
		data = data_result['dataPoints']

		sla_dict = {}
		entities = data_result['entities']
		for k,v in data.items():
			avg = np.mean([el[1] for el in v if el[1]])
			
			entity_ids = k.split(',')
			new_key = f'{entities[entity_ids[0].strip()]}, {entities[entity_ids[1].strip()]}'
			sla_dict[new_key] = avg
	except Exception as e:
		print(repr(e))

	return sla_dict

def write_csv(filename, data_dict, header, columns):
	with open(filename, 'a+') as csv_file:
		writer = csv.writer(csv_file, lineterminator='\n')
		writer.writerow([header])
		writer.writerow(columns)
		for k,v in data_dict.items():
			writer.writerow([k, v])
		writer.writerow([])

if __name__ == '__main__':
	# read config
	with open('config.json') as fp:
		config = json.load(fp)

	url = config.get('url')
	token = config.get('token')
	relative_time = 'month' # hour, day, month, week
	csv_filename = 'synthetic_sla.csv'
	timeseries = {
		'Synthetic Monitor': 'com.dynatrace.builtin%3Asyntheticmonitor.availability.percent',
		'HTTP Monitor': 'com.dynatrace.builtin%3Asynthetic.httpmonitor.availability.percent'
	}

	for display_name,t_id in timeseries.items():
		dt_json = dynatrace_api_request(url, token, t_id, relative_time)
		sla_dict = build_availability_dict(dt_json)
		csv_columns = ('Test Name, Location', 'Average availability (Percent)')
		csv_header = f'{display_name}: last {relative_time}'
		write_csv(csv_filename, sla_dict, csv_header, csv_columns)
