# Request synthetic data from the DT API
# Loop through each test + location
# Record the average for test availability
# Display each test name alongside average availability for the period

import json
import csv
import numpy as np
import requests

if __name__ == '__main__':
	with open('config.json') as fp:
		config = json.load(fp)

	dt_url = config.get('url')
	dt_token = config.get('token')
	timeseries_id = 'com.dynatrace.builtin%3Asyntheticmonitor.availability.percent'
	relative_time = 'day' # hour, day, month, week

	request_url = f'{dt_url}/api/v1/timeseries/{timeseries_id}?includeData=true&relativeTime={relative_time}'
	headers = { 
		'Accept': 'application/json', 
		'Authorization': f'Api-Token {dt_token}'
	}

	response = requests.get(request_url, headers=headers)
	response.raise_for_status()

	dt_json = response.json()
	data_result = dt_json['dataResult']
	data = data_result['dataPoints']

	sla_dict = {}
	entities = data_result['entities']
	for k,v in data.items():
		avg = np.mean([el[1] for el in v])
		
		entity_ids = k.split(',')
		new_key = f'{entities[entity_ids[0].strip()]}, {entities[entity_ids[1].strip()]}'
		sla_dict[new_key] = avg

	with open('synthetic_sla.csv', 'w') as csv_file:
		writer = csv.writer(csv_file, lineterminator='\n')
		writer.writerow(('Test Name, Location', 'Average availability (Percent)'))
		for k, v in sla_dict.items():
			writer.writerow([k, v])