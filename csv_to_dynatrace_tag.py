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
from datetime import datetime, timedelta
import pandas as pd
from pprint import pprint

def build_row_dict(row):
	# Name, Business_Rep, Tech_Rep, Critical, Site, Applications, AppFormatted, Security, Env
	host_data = {}
	try:
		host_data['name'] = row.Name
		host_data['business_rep'] = row.Business_Rep
		host_data['tech_rep'] = row.Tech_Rep,
		host_data['critical'] = row.Critical,
		host_data['site'] = row.Site,
		host_data['applications'] = row.Applications
		host_data['system'] = row.AppFormatted
		host_data['security_zone'] = row.Security
		host_data['env'] = row.Env
	except AttributeError as e:
		print(e)

	return host_data

if __name__ == '__main__':
	# read config
	with open('config_csv.json') as fp:
		config = json.load(fp)

	url = config.get('url')
	token = config.get('token')
	csv_file = config.get('csv_file')
	df = pd.read_csv(csv_file, engine='python')
	host_data_list = []
	for row in df.itertuples():
		host_data_list.append(build_row_dict(row))

	pprint(host_data_list)
