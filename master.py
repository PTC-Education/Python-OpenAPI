import json
import os

from onshape_client.client import Client
from onshape_client.onshape_url import OnshapeElement

from API_generator import generate_api, clean_url

import nbformat as nbf

# Setup Onshape Client with API keys
base = 'https://cad.onshape.com'
for _, _, files in os.walk('.'):
    if "OnshapeAPIKey.py" in files:  # Put API key in project folder
        exec(open("OnshapeAPIKey.py").read())
        break
client = Client(configuration={'base_url': base,
                               'access_key': access,
                               'secret_key': secret})

# Get all info from Onshape Open API
# Source (Glassworks): https://cad.onshape.com/glassworks/explorer/
headers = {'Accept': 'application/vnd.onshape.v2+json; charset=UTF-8;qs=0.1',
           'Content-Type': 'application/json'}
response = client.api_client.request(method='GET',
                                     url=base + '/api/openapi',
                                     query_params={},
                                     headers=headers,
                                     body={})
openApi = json.loads(response.data)

# Test out the functions
"""
endpoint = '/partstudios/d/{did}/{wvm}/{wvmid}/e/{eid}/features' 
call_type = 'post' 
api_py = generate_api(openApi, endpoint, call_type)
"""

# Start writing a Jupyter notebook
nb = nbf.v4.new_notebook()  # the notebook 
cells = []  # the cells in the notebook (ordered -> use append())

"""
To add text: nbf.v4.new_markdown_cell(text)
To add code: nbf.v4.new_code_cell(code)s
Then, append to cells 
"""

nb["cells"] = cells 
with open("Snippets.ipynb", 'w') as f: 
    nbf.write(nb, f)