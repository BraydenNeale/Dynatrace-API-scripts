"""
Generate list of known servers and expected tagging keys:
e.g. CSV: 
Hostname | Site | Zone | Application | Environment | System | Vendor | Unit |

Psuedo code:
For each row in the csv file
    Use the hostname column for the Dynatrace entity selector: type(host),tag("hostname:<HOST_NAME>”)
    For each additional column in the CSV (e.g. site, zone)
        Create an API tag with key=[API]<COLUMN_NAME> and value=<CELL_VALUE> (e.g. [API]Environment=PROD)
    Add each tag to the Dynatrace JSON format e.g.
        {
          "tags": [
            {
              "key": "[API]Environment",
              "value": "PROD"
            },
            {
              "key": "[API]Application",
              "value":"MyApp"
            }
          ]
        }
	[Optional] Delete existing keys from the tagging API (avoid duplicates and replace the old vals)
    Post json payload to the Dynatrace tagging API: /api/v2/tags?entitySelector=<ENTITY_SELECTOR> 
"""
import json
import requests
import logging
import urllib
import pandas as pd
import os

logging.basicConfig(
	filename='csv_to_tags.log',
	level=logging.INFO,
	format='%(asctime)s : %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

""""
DELETE all of the tags in Dynatrace
Run before CREATE to clean out existing tags (Dynatrace will create duplicates otherwise)
"""
def delete_tags_in_dynatrace(host_data_list, DYNATRACE_URL, DYNATRACE_TOKEN):
	logging.info('\n***** DELETING TAGS *****')
	api_path = f'{DYNATRACE_URL}/api/v2/tags?'
	delete_all_query = 'deleteAllWithKey=true'

	for dict in host_data_list:
		for selector,tags in dict.items():
			selector_query = f'entitySelector={urllib.parse.quote(selector)}'
			for tag in tags.get('tags'):
				key = tag.get('key')
				logging.info(f'{key} : {selector}')
				key_query = f'key={urllib.parse.quote(key)}'
				query_param = '&'.join([key_query, delete_all_query, selector_query])
				request_url = f'{api_path}{query_param}'
				try:
					dynatrace_delete_request(request_url, DYNATRACE_TOKEN)
				except requests.exceptions.HTTPError as e:
					# Might not be tagged... so just ignore and continue
					pass

"""
CREATE all of the tags in Dynatrace
"""
def create_tags_in_dynatrace(host_data_list, DYNATRACE_URL, DYNATRACE_TOKEN):
	logging.info('\n***** CREATING TAGS *****')
	api_path = f'{DYNATRACE_URL}/api/v2/tags?'
	for dict in host_data_list:
		for selector,tags in dict.items():
			query_param = f'entitySelector={urllib.parse.quote(selector)}'
			logging.info(f'Tagging: selector = {selector}')
			request_url = f'{api_path}{query_param}'
			try:
				dynatrace_post_request(request_url, DYNATRACE_TOKEN, tags)
			except requests.exceptions.HTTPError as e:
				logging.warning(e)

""""
GENERAL - Send a DELETE request to the Dynatrace API
"""
def dynatrace_delete_request(request_url, token):
	headers = { 
		'Accept': 'application/json', 
		'Authorization': f'Api-Token {token}'
	}
	response = requests.delete(request_url, headers=headers)
	response.raise_for_status()

""""
GENERAL - Send a POST request to the Dynatrace API
"""
def dynatrace_post_request(request_url, token, payload):
	headers = { 
		'Accept': 'application/json', 
		'Authorization': f'Api-Token {token}',
		'Content-type': 'application/json',
	}
	response = requests.post(request_url, data=json.dumps(payload), headers=headers)
	response.raise_for_status()

"""
Builds up the selector and tags for each csv row
FOMAT
'Selector' : {'tags': [{'key':'my_key', 'value':'my_value'}]}
e.g.
{'type(host),entityName.startsWith(hostname)': {'tags': [{'key': '[API]name',
                                                          'value': 'hostname'},
                                                         {'key': '[API]env',
                                                          'value': 'Prod'},
                                                         ]}},
"""
def build_row_dict(csv_mapping, row):
	row_dict = {}
	host_data = {}
	tag_list = []
	selector = None
		
	hostname = getattr(row, 'Name', None)
	if csv_cell_isvalid(hostname):
		#TODO improve this selector 
		#EntityName selector is at risk of name changes
		#but tags are case sensitive, so not reliable with data entry
		#type(host),entityName.startsWith(UATBLFM01)
		selector = f'type(host),entityName.startsWith({hostname})'
		for tag,csv_col in csv_mapping:
			tag_key = f'[API]{tag}'
			tag_value = getattr(row, csv_col, None)
			if csv_cell_isvalid(tag_value):
				tag_list.append({
					'key': tag_key,
					'value': tag_value
				})
			else:
				logging.warning(f'{hostname} - Invalid column: {csv_col}')
				
		logging.info(f'{hostname} - {tag_list}')
		host_data['tags'] = tag_list
		row_dict = {selector: host_data}
	
	return row_dict

def csv_cell_isvalid(cell):
	return (cell is not None) and (not pd.isnull(cell))

def log_config(DYNATRACE_URL, CSV_FILE, CREATE_TAGS, DELETE_TAGS):
	logging.info('\n***** CONFIG *****')
	logging.info(f'DYNATRACE_URL: {DYNATRACE_URL}')
	logging.info(f'CSV_FILE: {CSV_FILE}')
	logging.info(f'CREATE_TAGS: {CREATE_TAGS}')
	logging.info(f'DELETE_TAGS: {DELETE_TAGS}')

"""
Define the CSV columns to fetch
Using:
Name, Business_Rep, Tech_Rep, Critical, Site, 
Applications, AppFormatted, Security, Env
"""
def get_csv_tag_mapping():
	# (TAG_NAME, CSV_COLUMN_NAME)
	csv_tag_tuples = [
		('name', 'Name'),
		('domain', 'Domain'),
		('business_rep', 'Business_Rep'),
		('tech_rep', 'Tech_Rep'),
		('critical', 'Critical'),
		('site', 'Site'),
		('applications', 'Applications'),
		('system', 'AppFormatted'),
		('security_zone', 'Security_Zone_Level'),
		('env', 'Env')
	]
	logging.info('\n***** TAG -> CSV *****')
	logging.info(f'(TAG, CSV_COLUMN): {csv_tag_tuples}')
	return csv_tag_tuples

"""
Set config in config_csv.json (copy example_csv.json)
Usage: py .\csv_to_dynatrace_tag.py
"""
if __name__ == '__main__':
	log_file = logging.getLogger().handlers[0].baseFilename

	# Read config
	with open('config_csv.json') as fp:
		config = json.load(fp)

	URL_ENV_VAR = config.get('url')
	DYNATRACE_URL = os.environ.get(URL_ENV_VAR)
	TOKEN_ENV_VAR = config.get('token')
	DYNATRACE_TOKEN = os.environ.get(TOKEN_ENV_VAR)
	CSV_FILE = config.get('csv_file')
	CREATE_TAGS = config.get('create_tags')
	DELETE_TAGS = config.get('delete_tags')

	log_config(DYNATRACE_URL, CSV_FILE, CREATE_TAGS, DELETE_TAGS)

	csv_tag_tuples = get_csv_tag_mapping()

	# Load CSV and build tagging dictionary
	logging.info('\n***** BUILDING TAG DICTIONARY *****')
	print('Building tag dictionary')
	df = pd.read_csv(CSV_FILE, engine='python')
	host_data_list = []
	for row in df.itertuples():
		host_data_list.append(build_row_dict(csv_tag_tuples, row))
	
	# Dynatrace APIs
	if DELETE_TAGS:
		print('Deleting tags')
		delete_tags_in_dynatrace(host_data_list, DYNATRACE_URL, DYNATRACE_TOKEN)
	if CREATE_TAGS:
		print('Creating tags')
		create_tags_in_dynatrace(host_data_list, DYNATRACE_URL, DYNATRACE_TOKEN)
	
	print(f'Done - Check logs in "{logging.getLogger().handlers[0].baseFilename}"')