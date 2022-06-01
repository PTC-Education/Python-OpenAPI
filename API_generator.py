import json 
import copy
from typing import Dict
from onshape_client.onshape_url import OnshapeElement 


def clean_request_body(openApi: Dict, body: Dict, add_used: Dict) -> Dict: 
    """
    A recursion built to clean the request_body with all the "$ref"
    
    add_used: the addresses that have been used; avoid infinite recursion depth 
                if a component of the body allows multiple sub_components of the same 
                type as the mother component 
    address: the cleaned address; e.g., "BTMFeature-134"
    body: the retrieved request body, potentially with more refs inside
    """
    for key, item in body.items(): 
        # Reference to other schema inside a schema reference 
        if '$ref' in item: 
            address = item['$ref'].split('/')[-1]
            if address in add_used: 
                body[key] = "string"
            else: 
                add_used[address] = True 
                if 'properties' in openApi['components']['schemas'][address]: 
                    sub_body = copy.deepcopy(openApi['components']['schemas'][address]['properties'])
                    body[key] = clean_request_body(openApi, sub_body, add_used)
                else: 
                    if openApi['components']['schemas'][address]['type'] == 'object': 
                        body[key] = {}
                    elif openApi['components']['schemas'][address]['type'] == 'array': 
                        body[key] = []
                    else: 
                        body[key] = openApi['components']['schemas'][address]['type']
        # An array of items 
        elif item['type'] == 'array': 
            if '$ref' in item['items']: 
                address = item['items']['$ref'].split('/')[-1]
                if address in add_used:  
                    body[key] = ["string"]
                else: 
                    add_used[address] = True 
                    if 'properties' in openApi['components']['schemas'][address]: 
                        sub_body = copy.deepcopy(openApi['components']['schemas'][address]['properties'])
                        body[key] = [clean_request_body(openApi, sub_body, add_used)]
                    else: 
                        if openApi['components']['schemas'][address]['type'] == 'object': 
                            body[key] = {}
                        elif openApi['components']['schemas'][address]['type'] == 'array': 
                            body[key] = []
                        else: 
                            body[key] = openApi['components']['schemas'][address]['type']
            else: 
                body[key] = [item['items']['type']]
        # A dictionary of items 
        elif item['type'] == 'object': 
            temp_item = copy.deepcopy(item)
            if 'example' in item: 
                body[key] = temp_item['example']
            elif 'properties' in item: 
                body[key] = clean_request_body(openApi, temp_item['properties'], add_used)
            else: 
                del temp_item['type']
                body[key] = {}
        # Just an item of a specific data type 
        else: 
            body[key] = item['type']
    return body


def print_request_body(openApi: Dict, api_path: str, api_type="post") -> str: 
    """
    Generate the format of the request body of the API call in comment format. 
    It is meant to be used as a reference for the users, where more info can be found online. 
    """
    # General common description 
    output_format = '''# The following is the template of the request body of this API endpoint:'''
    if 'description' in openApi['paths'][api_path][api_type]['requestBody']: 
        output_format += '''
# Description: {}'''.format(openApi['paths'][api_path][api_type]['requestBody']['description'].replace('\n', ' '))

    # Look for specific data type 
    header = list(openApi['paths'][api_path][api_type]['requestBody']['content'].keys())[0]
    schema = openApi['paths'][api_path][api_type]['requestBody']['content'][header]['schema']
    # A referred schema 
    if "$ref" in schema: 
        body_address = openApi['paths'][api_path][api_type]['requestBody']['content'][header]['schema']['$ref']
        body_address = body_address.split('/')[-1]
        used_address = {body_address: True}
        if 'properties' in openApi['components']['schemas'][body_address]: 
            request_body = copy.deepcopy(openApi['components']['schemas'][body_address]["properties"])
        else: 
            body_address = openApi['components']['schemas'][body_address]['allOf'][0]['$ref']
            body_address = body_address.split('/')[-1]
            used_address[body_address] = True 
            request_body = copy.deepcopy(openApi['components']['schemas'][body_address]['properties'])
        request_body = clean_request_body(openApi, request_body, used_address)
        output_format += '''
"""
{}
"""

        '''.format(json.dumps(request_body, indent=4, sort_keys=True))
    # No schema used 
    else: 
        output_format += '''
# The request body for this API endpoint is a {}
        '''.format(schema['type'])
    
    return output_format


def clean_url(url: str, fixed_url: str) -> str: 
    """
    Clean up the URL that the user copies from the Onshape document to match the required fixed_url for the API call. 
    Required to be put in the main code for use to support each API endpoint. 
    """
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


def generate_api(openApi: Dict, api_path: str, api_type: str) -> str: 
    """
    This function retrieves all required and optional components for a REST API call in Onshape 
    Source info (Glassworks): https://cad.onshape.com/glassworks/explorer/ 
    
    openApi: the source JSON, containing all info about API endpoints for Onshape 
    api_path: the title of the API endpoint on Glassworks 
    api_type: the tag for the API endpiont on Glassworks ("GET", "POST", "DELETE")
    """
    api_path = api_path.strip()
    api_type = api_type.strip().lower()

    # Info about the API endpoint for labelling 
    func_tag = openApi['paths'][api_path][api_type]['tags'][0]
    func_name = openApi['paths'][api_path][api_type]['operationId']
    if 'summary' in openApi['paths'][api_path][api_type]:  
        func_descrip = openApi['paths'][api_path][api_type]['summary'].replace('\n', ' ')
    else: 
        func_descrip = ""

    func_format = '''#@title Function `{}()` (type `{}`)
#@markdown {}
#@markdown More details can be found in https://cad.onshape.com/glassworks/explorer/#/{}/{}
def {}(client=client): 
    method = "{}"
    '''.format(func_name, api_type.upper(), func_descrip, func_tag, func_name, func_name, api_type.upper())

    # URL path 
    func_format += '''
    #@markdown Copy and paste the URL of the Onshape document (Required): 
    url = "" #@param{{type: "string"}}
    cleaned_url = clean_url(url, '{}')
    '''.format(api_path)

    # Query parameters 
    if 'parameters' in openApi['paths'][api_path][api_type]: 
        params = openApi['paths'][api_path][api_type]['parameters']
        for param in params:     
            if param['name'] not in ["did", 'wvmid', 'wvid', 'wid', 'eid', 'wvm', 'wv']:  # already addressed with the URL
                # Start with the description of the parameter 
                if "description" in param: 
                    func_format += '''
    #@markdown {} '''.format(param["description"].replace('\n', ' '))
                else: 
                    func_format += '''
    #@markdown '''
                # If this parameter is required 
                if "required" in param: 
                    func_format += '''(Required): '''
                else: 
                    func_format += '''(Optional): '''
                if param['name'] == "If-None-Match":  # a special case (- causes error in python)
                    func_format += '''
    If_None_Match = '' #@param{"type": "string"}'''
                else: 
                    # Format the paramter with its required data type, or its default value if available 
                    if "default" in param["schema"]: 
                        if param['schema']['type'] == 'string': 
                            func_format += '''
    {} = '{}' #@param {{"type": '{}'}}'''.format(param["name"], param["schema"]["default"], param["schema"]["type"])
                        else:
                            func_format += '''
    {} = {} #@param {{"type": '{}'}}'''.format(param["name"], param["schema"]["default"], param["schema"]["type"])
                    else: 
                        if param["schema"]["type"] == "string": 
                            func_format += '''
    {} = "" #@param {}'''.format(param["name"], param["schema"])
                        elif param["schema"]["type"] == "number": 
                            func_format += '''
    {} = 0 #@param {}'''.format(param["name"], param["schema"])
                        else:  # Colab doesn't take some data types as a field type (e.g., array)
                            func_format += '''
    #@markdown (Data type: {})
    {} = None #@param {{'type': 'raw'}}'''.format(param["schema"], param["name"])
                # Add extra components to the cleaned_url (e.g., feature ID)
                if param["in"] == "path": 
                    func_format += '''
    cleaned_url.replace('{{{}}}', {})
                    '''.format(param["name"], param["name"])
    # If no parameters is required 
    else: 
        params = None 
        func_format += '''
    # No parameters. '''
    
    # Putting all parameters together for the API call (only include if not None)
    func_format += '''

    params = {}'''
    if params:  # only if there are parameters 
        for param in params: 
            if "id" not in param["name"] and param['name'] != "wvm" and param['name'] != 'wv': 
                if param['name'] == "If-None-Match":  # a special case 
                    func_format += '''
    if If_None_Match: 
        params["If-None-Match"] = If_None_Match'''
                else: 
                    if param["schema"]["type"] != "boolean": 
                        func_format += '''
    if {}: 
        params["{}"] = {}'''.format(param["name"], param["name"], param["name"])
                    else: 
                        func_format += '''
    params["{}"] = {}'''.format(param["name"], param["name"])
    
    # Headers 
    if 'default' in openApi['paths'][api_path][api_type]['responses']: 
        if list(openApi['paths'][api_path][api_type]['responses']['default']['content'].keys()): 
            func_format += '''
    
    headers = {{"Accept": "{}", "Content-Type": "application/json"}}
            '''.format(list(openApi['paths'][api_path][api_type]['responses']['default']['content'].keys())[0])
        else: 
            func_format += '''
            
    headers = {}
            '''
    elif '200' in openApi['paths'][api_path][api_type]['responses']: 
        if 'content' in openApi['paths'][api_path][api_type]['responses']['200']: 
            func_format += '''
            
    headers = {{"Accept": "{}", "Content-Type": "application/json"}}
            '''.format(list(openApi['paths'][api_path][api_type]['responses']['200']['content'].keys())[0])
        else: 
            func_format += '''
            
    headers = {} 
            '''
    else: 
        func_format += '''
        
    headers = {}
        '''

    # Body 
    # Only required for certain "POST" calls 
    if api_type == 'post' and 'requestBody' in openApi['paths'][api_path][api_type]: 
        body_type = {True: "Required", False: "Optional"}
        func_format += '''
    #@markdown Define payload or modify the template `requestBody` above ({})
    payload = None #@param{{'type': 'raw'}}
        '''.format(body_type['required' in openApi['paths'][api_path][api_type]['requestBody']])
        body_output = print_request_body(openApi, api_path)  # the template on top of the actual function 
    # No payload is required for "GET" and "DELETE" calls 
    else: 
        body_output = None 
        func_format += '''
    payload = {}
        '''
    
    # Make the call 
    func_format += '''
    response = client.api_client.request(method, url=cleaned_url, query_params=params, headers=headers, body=payload)
    parsed = json.loads(response.data)
    
    #@markdown Do you want to print out the response of this API call? 
    show_response = False #@param {'type': 'boolean'}
    if show_response: 
        print(json.dumps(parsed, indent=4, sort_keys=True)) 
    
    return parsed 
    '''

    if body_output: 
        func_format = body_output + func_format
    return func_format 
