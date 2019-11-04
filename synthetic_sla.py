# Request synthetic data from the DT API
# Loop through each test + location
# Record the average for test availability
# Display each test name alongside average availability for the period

import json
import pandas
import requests

if __name__ == '__main__':
	with open('config.json') as fp:
		config = json.load(fp)


	dt_url = config.get('url')
	dt_token = config.get('token')
	timeseries_id = 'com.dynatrace.builtin%3Asyntheticmonitor.availability.percent'
	relative_time = 'hour'


	request_url = f'{dt_url}/api/v1/timeseries/{timeseries_id}?relativeTime={relative_time}'
	headers = { 
		'Accept': 'application/json', 
		'Authorization': f'Api-Token {dt_token}'
	}

	response = requests.get(request_url, headers=headers)
	response.raise_for_status()





