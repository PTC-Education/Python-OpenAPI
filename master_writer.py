import json
import os
import nbformat as nbf

from onshape_client.client import Client
from API_generator import generate_api, clean_url


# Setup Onshape Client with API keys
base = 'https://cad.onshape.com'
access = ""
secret = "" 
for _, _, files in os.walk('.'):
    if "OnshapeAPIKey.py" in files:  # Put API key in project folder
        exec(open("OnshapeAPIKey.py").read())
        break
client = Client(configuration={'base_url': base,
                               'access_key': access,
                               'secret_key': secret})

# Get all info from Onshape Open API
# Source (Glassworks): https://cad.onshape.com/glassworks/explorer/
response = client.api_client.request(method='GET',
                                     url=base + '/api/openapi',
                                     query_params={},
                                     headers={},
                                     body={})
openApi = json.loads(response.data)

###################### Start writing the Jupyter notebook #########################
nb = nbf.v4.new_notebook()  # the notebook 
cells = []  # the cells in the notebook (ordered -> use append())

"""
To add text: nbf.v4.new_markdown_cell(text)
To add code: nbf.v4.new_code_cell(code)
Then, append to cells 
"""

# General info as an introduction 
cells.append(nbf.v4.new_markdown_cell('''# Onshape REST API 
Below is the Python version of all the Onshape REST API endpoints in the form of code snippets. You can follow guidance in [this GitHub repository](https://github.com/PTC-Education/Python-OpenAPI) to import these snippets in your own Jupyter notebook using Google Colab. Meanwhile, the official full documentation of all API endpoints can be found on [this website](https://cad.onshape.com/glassworks/explorer/). 

Note: this Jupyter notebook is designed to be launched and used in Google Colab for the best experience. 
'''))

cells.append(nbf.v4.new_markdown_cell('''# 0. Setup
**Important:** you have to run ALL cells in this section before you can properly use the rest of the code snippets. When importing snippets to your own Jupyter notebook, you have to import ALL cells in this section and run them before executing any of the snippets in this notebook. 
'''))

cells.append(nbf.v4.new_code_cell('''#@title Import and Setup Onshape Client
!pip install onshape-client
from onshape_client.client import Client
from onshape_client.onshape_url import OnshapeElement
import json

#@markdown Chage the base if using an enterprise (i.e. "https://ptc.onshape.com")
base = 'https://cad.onshape.com' #@param {type:"string"}

#@markdown Would you like to import your API keys from a file, or copy and paste them directly?
keyImportOption = "Upload Keys from File" #@param ["Upload Keys from File", "Copy/Paste Keys"]

from IPython.display import clear_output 
clear_output()
print("Onshape Client successfully imported!")

if keyImportOption == "Upload Keys from File":
    from google.colab import files
    uploaded = files.upload()
    for fn in uploaded.keys():
        execfile(fn)

    client = Client(configuration={"base_url": base, 
                                   "access_key": access, 
                                   "secret_key": secret})
    clear_output()
    print('Onshape client configured - ready to go!')
else:
    access = input("Paste your Onshape Access Key: ")
    secret = input("Paste your Onshape Secret Key: ")
    client = Client(configuration={"base_url": base, 
                                   "access_key": access, 
                                   "secret_key": secret})
    clear_output()
    print('Onshape client configured - ready to go!')
'''))

cells.append(nbf.v4.new_code_cell('''#@title Import and run these helper functions for future use 
def clean_url(url: str, fixed_url: str) -> str: 
    element = OnshapeElement(url)
    base = element.base_url 
    if '{did}' in fixed_url: 
        fixed_url = fixed_url.replace('{did}', element.did)

    if '{wvm}' in fixed_url: 
        fixed_url = fixed_url.replace('{wvm}', element.wvm)
    elif '{wv}' in fixed_url: 
        fixed_url = fixed_url.replace('{wv}', element.wvm)

    if '{wvmid}' in fixed_url: 
        fixed_url = fixed_url.replace('{wvmid}', element.wvmid)
    elif '{wvid}' in fixed_url: 
        fixed_url = fixed_url.replace('{vwid}', element.wvmid)
    elif '{wid}' in fixed_url: 
        fixed_url = fixed_url.replace('{wid}', element.wvmid)

    if '{eid}' in fixed_url: 
        fixed_url = fixed_url.replace('{eid}', element.eid)

    return base + "/api" + fixed_url 
'''))

# A list of all API endpoint paths 
endpoints = list(openApi['paths'].keys())  # each item is a str 

# A list of all API categories 
temp_tags = openApi['tags']  # each item is a dict {'name': str, 'description': str}
tags = {}  # dict{name: description}
# Note that temp_tags is in alphebatical order (not the same for endpoints)
for item in temp_tags: 
    tags[item['name']] = item['description']

curr_tag = "None"
tag_ind = 0

for endpoint in endpoints: 
    # All types of the endpoint (get, post, delete)
    api_type = list(openApi['paths'][endpoint].keys()) 
    # Check if need to start a new section 
    if openApi['paths'][endpoint][api_type[0]]['tags'][0] != curr_tag: 
        tag_ind += 1
        curr_tag = openApi['paths'][endpoint][api_type[0]]['tags'][0]
        if curr_tag in tags: 
            tag_descript = tags[curr_tag]
        else: 
            tag_descript = None 
        cells.append(nbf.v4.new_markdown_cell('''# {}. {}
{} 
        '''.format(tag_ind, curr_tag, tag_descript)))
    # Generate and add code for each type of the endpoint 
    for typ in api_type: 
        try: 
            cells.append(nbf.v4.new_code_cell('''{}'''.format(generate_api(openApi, endpoint, typ))))
        except: 
            print("Error encountered for endpoint:", endpoint, typ)


# Write all the cells in a Jupyter notebook 
nb["cells"] = cells  # add cells to notebook 
with open("API_Snippets.ipynb", 'w') as f: 
    nbf.write(nb, f)  # write the notebook 
print("Notebook created successfully!")
