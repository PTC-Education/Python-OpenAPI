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
    output_format = ""
    if 'description' in openApi['paths'][api_path][api_type]['requestBody']: 
        output_format += '''
                Description: {}'''.format(openApi['paths'][api_path][api_type]['requestBody']['description'].replace('\n', ' '))

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
{}
        '''.format(json.dumps(request_body, indent=4, sort_keys=True))
    # No schema used 
    else: 
        output_format += '''
                The request body for this API endpoint is a {}'''.format(schema['type'])
    
    return output_format


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
    required = {True: "Required", False: "Optional"}

    # Body 
    try: 
        if 'required' in openApi['paths'][api_path][api_type]['requestBody']: 
            body_arg = 'payload'
        else: 
            body_arg = 'payload={}'
    except KeyError: 
        body_arg = 'payload={}'

    # Description 
    func_tag = openApi['paths'][api_path][api_type]['tags'][0]
    func_name = openApi['paths'][api_path][api_type]['operationId']
    if 'summary' in openApi['paths'][api_path][api_type]: 
        func_descrip = openApi['paths'][api_path][api_type]['summary'].replace('\n', ' ')
    else: 
        func_descrip = ""
    func_intro = '''#@title `{}` (type `{}`)
def {}(client, url, {}, params={{}}, show_response=False): 
    """
    API call type: `{}`
    {}
    More details can be found in https://cad.onshape.com/glassworks/explorer/#/{}/{}

    - `client` (Required): the Onshape client configured with your API keys
    - `url` (Required): the url of the Onshape document you would like to make this API call to'''.format(
        func_name, api_type.upper(), func_name, body_arg, 
        api_type.upper(), func_descrip, func_tag, func_name)
    
    # Start defining the function 
    func_code = '''
    method = "{}" '''.format(api_type.upper())

    # URL path 
    func_code += '''
    element = OnshapeElement(url)
    base = element.base_url
    fixed_url = "/api{}"'''.format(api_path)
    
    # Query parameters     
    if 'parameters' in openApi['paths'][api_path][api_type]: 
        func_intro += '''
    - `params`: a dictionary of the following parameters for the API call'''
        params = openApi['paths'][api_path][api_type]['parameters']
        for param in params: 
            if param['in'] == "path": 
                if param['name'] == 'did': 
                    func_code += '''
    fixed_url = fixed_url.replace('{did}', element.did)'''
                elif param['name'] in ['wvm', 'wv', 'wm']: 
                    func_code += '''
    fixed_url = fixed_url.replace('{{{}}}', element.wvm)'''.format(param['name'])
                elif param['name'] in ['wvmid', 'wvid', 'wmid', 'wid']: 
                    func_code += '''
    fixed_url = fixed_url.replace('{{{}}}', element.wvmid)'''.format(param['name'])
                elif param['name'] == 'eid': 
                    func_code += '''
    fixed_url = fixed_url.replace('{eid}', element.eid)'''
                else: 
                    func_code += '''
    fixed_url = fixed_url.replace('{{{}}}', params["{}"])
    del params["{}"]'''.format(param["name"], param["name"], param["name"])
                    if 'description' in param: 
                        func_intro += '''
        - `{}` (Required): {}'''.format(param['name'], param['description'].replace('\n', ' '))
                    else: 
                        func_intro += '''
        - `{}` (Required)'''.format(param['name'])
            else:
                if param['name'] == 'If-None-Match':  # special case
                    func_intro += '''
        - `If-None-Match`: string'''
                else: 
                    if 'description' in param: 
                        param_descrip = ": " + param['description']
                    else: 
                        param_descrip = "" 
                    if 'default' in param['schema']: 
                        param_default = "(default: " + str(param['schema']['default']) + ')'
                    else: 
                        param_default = ''
                    func_intro += '''
        - `{}`: {} ({}){} {}'''.format(param['name'], 
                                    param['schema']['type'], 
                                    required['required' in param], 
                                    param_descrip, 
                                    param_default)
    else: 
        func_intro += '''
    - `params={}`: no params accepted for this API call. '''
            
    # Body 
    if api_type == 'post' and 'requestBody' in openApi['paths'][api_path][api_type]: 
        func_intro += '''
    - `payload` ({}): a dictionary of the payload body of this API call; a template of the body is shown below: {}'''.format(
        required['required' in openApi['paths'][api_path][api_type]['requestBody']], print_request_body(openApi, api_path))
    else: 
        func_intro += '''
    - `payload={}`: no payload body is accepted for this API call'''

    # Headers 
    if 'default' in openApi['paths'][api_path][api_type]['responses']: 
        if list(openApi['paths'][api_path][api_type]['responses']['default']['content'].keys()): 
            func_code += '''
    headers = {{"Accept": "{}", "Content-Type": "application/json"}}
            '''.format(list(openApi['paths'][api_path][api_type]['responses']['default']['content'].keys())[0])
        else: 
            func_code += '''
    headers = {{}}
            '''.format(None)
    elif '200' in openApi['paths'][api_path][api_type]['responses']: 
        if 'content' in openApi['paths'][api_path][api_type]['responses']['200']: 
            func_code += '''
    headers = {{"Accept": "{}", "Content-Type": "application/json"}}
            '''.format(list(openApi['paths'][api_path][api_type]['responses']['200']['content'].keys())[0])
        else: 
            func_code += '''
    headers = {{}}
            '''.format(None)
    else: 
        func_code += '''
    headers = {{}}
        '''.format(None)
    
    # Make the call 
    func_code += '''
    response = client.api_client.request(method, url=base + fixed_url, query_params=params, headers=headers, body=payload)
    parsed = json.loads(response.data)
    if show_response: 
        print(json.dumps(parsed, indent=4, sort_keys=True)) 
    return parsed 
    '''.format(None)

    output = func_intro + '''
    - `show_response`: boolean: do you want to print out the response of this API call (default: False)
    """'''+ func_code 
    return output
