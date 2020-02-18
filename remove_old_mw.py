# Request synthetic data from the DT API
# Loop through each test + location
# Record the average for test availability
# Display each test name alongside average availability for the period

import json
import csv
import numpy as np
import requests
import pprint
import logging
from datetime import datetime, timedelta

logging.basicConfig(
	filename='deleted_Maintenance_Windows.log', 
	level=logging.INFO,
	format='%(asctime)s : %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
pp = pprint.PrettyPrinter()

def dynatrace_api_request(url, token, request):
	request_url = f'{url}{request}'
	headers = { 
		'Accept': 'application/json', 
		'Authorization': f'Api-Token {token}'
	}

	response = requests.get(request_url, headers=headers)
	response.raise_for_status()

	return response.json()

def get_old_mw_ids(mw_array, num_days_ago=10):
	mw_ids = []
	for mw in mw_array:
		mw_ids.append(mw['id'])

	old_date = datetime.now() - timedelta(days=num_days_ago)
	old_mw_ids = []
	logging.info('Deleting the following maintenance windows:')
	for mw_id in mw_ids:
		request = f'/api/config/v1/maintenanceWindows/{mw_id}'
		mw_id_json = dynatrace_api_request(url, token, request)
		mw_end_time = datetime.strptime(mw_id_json['schedule']['end'], '%Y-%m-%d %H:%M')
		if old_date > mw_end_time:
			old_mw_ids.append(mw_id)
			logging.info(mw_id_json)

	return old_mw_ids

def delete_mw_ids(mw_ids, url, token):
	for mw_id in mw_ids:
		delete_mw_id(mw_id, url, token)

def delete_mw_id(mw_id, url, token):
	request = f'/api/config/v1/maintenanceWindows/{mw_id}'
	request_url = f'{url}{request}'
	headers = { 
		'Accept': 'application/json', 
		'Authorization': f'Api-Token {token}'
	}

	response = requests.delete(request_url, headers=headers)
	response.raise_for_status()
	
	logging.info(f'DELETED: {mw_id}')

if __name__ == '__main__':
	# read config
	with open('config_mw.json') as fp:
		config = json.load(fp)

	url = config.get('url')
	token = config.get('token')

	mw_get = '/api/config/v1/maintenanceWindows'

	mw_json = dynatrace_api_request(url, token, mw_get)
	old_mw_ids = get_old_mw_ids(mw_json['values'], 5)
	delete_mw_ids(old_mw_ids, url, token)






