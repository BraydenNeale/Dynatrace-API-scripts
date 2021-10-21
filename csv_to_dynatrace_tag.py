# Generate list of known servers and expected tagging keys:
# e.g. CSV: 
# Hostname | Site | Zone | Application | Environment | System | Vendor | Unit |

# For each Item in the list:
#     use hostname column for the entity selector: type(host),tag("hostname:<HOST_NAME>”)
#     For each additional column in the CSV (e.g. site, zone)
#         Create an API tag with key=[API]<COLUMN_NAME> and value=<CELL_VALUE> (e.g. [API]Environment=PROD)
#     Add each tag to JSON e.g.
#         {
#           "tags": [
#             {
#               "key": "[API]Environment",
#               "value": "PROD"
#             },
#             {
#               "key": "[API]Application",
#               "value":"MyApp"
#             }
#           ]
#         }
#     Post json payload to the Dynatrace tagging API: /api/v2/tags?entitySelector=<ENTITY_SELECTOR> 
import json
import requests
import logging
import urllib
import pandas as pd
from pprint import pprint

logging.basicConfig(
	filename='csv_to_tags.log',
	level=logging.INFO,
	format='%(asctime)s : %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

def delete_tags_in_dynatrace(host_data_list, DYNATRACE_URL, DYNATRACE_TOKEN):
	api_path = f'{DYNATRACE_URL}/api/v2/tags?'
	delete_all_query = 'deleteAllWithKey=true'

	for dict in host_data_list:
		for selector,tags in dict.items():
			selector_query = f'entitySelector={urllib.parse.quote(selector)}'
			for tag in tags.get('tags'):
				key = tag.get('key')
				pprint(f'{key} - {selector}')
				key_query = f'key={urllib.parse.quote(key)}'
				query_param = '&'.join([key_query, delete_all_query, selector_query])
				request_url = f'{api_path}{query_param}'
				#pprint(request_url)
				try:
					dynatrace_delete_request(request_url, DYNATRACE_TOKEN)
				except requests.exceptions.HTTPError as e:
					# Might not be tagged... so just ignore and continue
					pass

def create_tags_in_dynatrace(host_data_list, DYNATRACE_URL, DYNATRACE_TOKEN):
	api_path = f'{DYNATRACE_URL}/api/v2/tags?'
	for dict in host_data_list:
		for selector,tags in dict.items():
			query_param = f'entitySelector={urllib.parse.quote(selector)}'
			
			request_url = f'{api_path}{query_param}'
			dynatrace_post_request(request_url, DYNATRACE_TOKEN, tags)

def dynatrace_delete_request(request_url, token):
	headers = { 
		'Accept': 'application/json', 
		'Authorization': f'Api-Token {token}'
	}
	response = requests.delete(request_url, headers=headers)
	response.raise_for_status()

def dynatrace_post_request(request_url, token, payload):
	headers = { 
		'Accept': 'application/json', 
		'Authorization': f'Api-Token {token}',
		'Content-type': 'application/json',
	}
	response = requests.post(request_url, data=json.dumps(payload), headers=headers)
	response.raise_for_status()

def build_row_dict(row):
	# Name, Business_Rep, Tech_Rep, Critical, Site, Applications, AppFormatted, Security, Env
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
		('security_zone', 'Security'),
		('env', 'Env')
	]

	host_data = {}
	try:
		#TODO improve this - tags are case sensitive
		#type(host),entityName.startsWith(UATBLFM01)
		selector = f'type(host),entityName.startsWith({row.Name})'

		tag_list = []
		for tag_tuple in csv_tag_tuples:
			tag_list.append({
				'key': f'[API]{tag_tuple[0]}',
				'value': getattr(row, tag_tuple[1])
			})
	except AttributeError as e:
		print(e)

	host_data['tags'] = tag_list
	return {selector: host_data}

if __name__ == '__main__':
	# read config
	with open('config_csv.json') as fp:
		config = json.load(fp)

	DYNATRACE_URL = config.get('url')
	DYNATRACE_TOKEN = config.get('token')
	CSV_FILE = config.get('csv_file')
	CREATE_TAGS = config.get('create_tags')
	DELETE_TAGS = config.get('delete_tags')

	# Load CSV and build tagging dictionary
	df = pd.read_csv(CSV_FILE, engine='python')
	host_data_list = []
	for row in df.itertuples():
		host_data_list.append(build_row_dict(row))
	
	# Dynatrace APIs
	if DELETE_TAGS:
		delete_tags_in_dynatrace(host_data_list, DYNATRACE_URL, DYNATRACE_TOKEN)
	if CREATE_TAGS:
		create_tags_in_dynatrace(host_data_list, DYNATRACE_URL, DYNATRACE_TOKEN)
	