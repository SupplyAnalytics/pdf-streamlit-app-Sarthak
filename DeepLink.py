from __future__ import with_statement
from AnalyticsClient import AnalyticsClient
import pandas as pd
import requests
import json
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

def ExportPivotMaster():
    class Config:
        CLIENTID = "1000.DQ32DWGNGDO7CV0V1S1CB3QFRAI72K"
        CLIENTSECRET = "92dfbbbe8c2743295e9331286d90da900375b2b66c"
        REFRESHTOKEN = "1000.0cd324af15278b51d3fc85ed80ca5c04.7f4492eb09c6ae494a728cd9213b53ce"
        ORGID = "60006357703"
        VIEWID = "174857000103970765"
        WORKSPACEID = "174857000004732522"

    class Sample:
        def __init__(self, ac):
            self.ac = ac

        def export_data(self):
            response_format = "csv"
            file_path_template = "BijnisDeeplinkPDF.csv"
            bulk = self.ac.get_bulk_instance(Config.ORGID, Config.WORKSPACEID)

            for view_id in view_ids:
                file_path = file_path_template.format(view_id)
                bulk.export_data(view_id, response_format, file_path)

    try:
        ac = AnalyticsClient(Config.CLIENTID, Config.CLIENTSECRET, Config.REFRESHTOKEN)
        obj = Sample(ac)
        view_ids = ["174857000103970765"]
        obj.export_data()
    except Exception as e:
        print(str(e))

ExportPivotMaster()

# Verify if the CSV file was created
csv_file = 'BijnisDeeplinkPDF.csv'
if not os.path.exists(csv_file):
    print(f"Error: File '{csv_file}' not found. Please check the export process.")
    exit(1)

# Read the CSV file
data = pd.read_csv(csv_file)

# URL and headers for the API request
url = 'https://api.bijnis.com/g/ba/generate/pdplink/'
headers = {
    'Content-Type': 'application/json'
}

# Initialize a list to hold all the responses
responses = []

# Function to handle individual requests
def make_request(variant_id):
    # Create the payload as specified in the cURL command
    payload = {
        "nid": [variant_id],
        "utmSource": "BI_Campaign",
        "utmCampaign": "BI_Campaign",
        "utmMedium": "BI_Campaign"
    }

    # Make the POST request
    response = requests.post(url, headers=headers, json=payload)

    # Add error handling
    if response.status_code == 200:
        return {'variantId': variant_id, 'response': response.json()}
    else:
        return {'variantId': variant_id, 'error': response.status_code}

# Use ThreadPoolExecutor to make parallel requests
with ThreadPoolExecutor(max_workers=100) as executor:
    # Submit tasks to the executor
    futures = {executor.submit(make_request, int(row['VariantId'])): int(row['VariantId']) for _, row in data.iterrows()}

    # Use tqdm to display a progress bar
    for future in tqdm(as_completed(futures), total=len(futures)):
        responses.append(future.result())

# Write all responses to a JSON file
json_file = 'output.json'
with open(json_file, 'w') as outfile:
    json.dump(responses, outfile, indent=4)

print("Data fetching complete. Responses saved to output.json.")

# Verify if the JSON file was created
if not os.path.exists(json_file):
    print(f"Error: File '{json_file}' not found. Please check the path.")
    exit(1)

# Read the JSON file and extract the required data
final_data = []

try:
    with open(json_file, 'r') as file:
        data = json.load(file)

        # Iterate through each JSON object in the array
        for item in data:
            # Extract variantId
            variant_id = item['variantId']

            # Check if 'response' and 'url' keys exist
            if 'response' in item and 'url' in item['response']:
                url = item['response']['url'][str(variant_id)]  # Access URL using variantId as key
                final_data.append({'VariantId': variant_id, 'App_Deeplink': url})
            else:
                print(f"Warning: Missing 'response' or 'url' key in item with variantId: {variant_id}")

    # Create pandas DataFrame and save to CSV (if data was extracted)
    if final_data:
        df = pd.DataFrame(final_data)
        df.to_csv('Postman_Deeplink_Final.csv', index=False)
        print('Success! CSV file created.')
    else:
        print("Warning: No data extracted due to missing keys in JSON objects.")
except FileNotFoundError:
    print(f"Error: File '{json_file}' not found. Please check the path.")
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON data from '{json_file}'.")



# def import_data():
#     class Config:

#         CLIENTID = "1000.DQ32DWGNGDO7CV0V1S1CB3QFRAI72K";
#         CLIENTSECRET = "92dfbbbe8c2743295e9331286d90da900375b2b66c";
#         REFRESHTOKEN = "1000.0cd324af15278b51d3fc85ed80ca5c04.7f4492eb09c6ae494a728cd9213b53ce";

#         ORGID = "60006357703";
#         WORKSPACEID = "174857000004732522";
#         VIEWID = "174857000098515113";

#     class sample:

#         ac = AnalyticsClient(Config.CLIENTID, Config.CLIENTSECRET, Config.REFRESHTOKEN)

#         def import_data(self, ac):
#             import_type = "APPEND"
#             file_type = "csv"
#             auto_identify = "true"
#             file_path = 'Postman_Deeplink_Final.csv'
#             bulk = ac.get_bulk_instance(Config.ORGID, Config.WORKSPACEID)
#             result = bulk.import_data(Config.VIEWID, import_type,file_type, auto_identify, file_path)        
#             print(result)

#     try:
#         obj = sample()
#         obj.import_data(obj.ac);

#     except Exception as e:
#         print(str(e))

# import_data()


