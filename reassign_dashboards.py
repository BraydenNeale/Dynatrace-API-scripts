# Get all dashboards owned by a specific user
# Reassign them to be owned by a new user

import json
import requests
import logging

logging.basicConfig(
	filename='reassigned_dashboards.log',
	level=logging.INFO,
	format='%(asctime)s : %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

def dynatrace_api_request(url, token, request):
	request_url = f'{url}{request}'
	headers = { 
		'Accept': 'application/json', 
		'Authorization': f'Api-Token {token}'
	}

	response = requests.get(request_url, headers=headers)
	response.raise_for_status()

	return response.json()

def get_old_owner_dashboards(old_user, db_array):
	db_ids = []
	logging.info('Reassigning the following dashboards:')
	for db in db_array:
		if db['owner'] == old_user: 
			db_ids.append(db['id'])
			logging.info(db)

	return db_ids

def reassign_old_owner_dashboards(old_db_ids, new_user, url, token):
	for db_id in old_db_ids:
		reassign_old_owner_dashboard(db_id, new_user, url, token)

def reassign_old_owner_dashboard(db_id, new_user, url, token):
	request = f'/api/config/v1/dashboards/{db_id}'

	dashboard_json = dynatrace_api_request(url, token, request)
	dashboard_json['dashboardMetadata']['owner'] = new_user
	
	put_request_url = f'{url}{request}'
	headers = { 
		'Content-type':'application/json',
		'Accept': 'application/json', 
		'Authorization': f'Api-Token {token}'
	}
	response = requests.put(put_request_url, json.dumps(dashboard_json), headers=headers)
	response.raise_for_status()

	logging.info(f'REASSIGNED: {db_id}')

if __name__ == '__main__':
	# read config
	with open('config_dashboard.json') as fp:
		config = json.load(fp)

	url = config.get('url')
	token = config.get('token')
	old_user = config.get('old_user')
	new_user = config.get('new_user')

	logging.info(f'Dashboards owned by {old_user} are being reassigned to {new_user}')
	dashboard_get = '/api/config/v1/dashboards'

	dashboard_json = dynatrace_api_request(url, token, dashboard_get)
	old_db_ids = get_old_owner_dashboards(old_user, dashboard_json['dashboards'])
	reassign_old_owner_dashboards(old_db_ids, new_user, url, token)
