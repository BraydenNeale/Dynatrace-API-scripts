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
from datetime import datetime, timedelta
import pandas as pd
from pprint import pprint

def create_tags_in_dynatrace(host_data_list, DYNATRACE_URL, DYNATRACE_TOKEN):
	api_path = f'{DYNATRACE_URL}/api/v2/tags?'
	for dict in host_data_list:
		for selector,tags in dict.items():
			query_param = f'entitySelector={urllib.parse.quote(selector)}'
			
			request_url = f'{api_path}{query_param}'
			dynatrace_post_request(request_url, DYNATRACE_TOKEN, tags)

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
	df = pd.read_csv(CSV_FILE, engine='python')
	host_data_list = []
	for row in df.itertuples():
		host_data_list.append(build_row_dict(row))

	create_tags_in_dynatrace(host_data_list, DYNATRACE_URL, DYNATRACE_TOKEN)
	
