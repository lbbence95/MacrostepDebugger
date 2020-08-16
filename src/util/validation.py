# Contains validation functions.

import json

def ValidateJSONValues(request_data):
    """Validates if the necessary keys have proper values.

    Args:
        request_data (request): A request containing the JSON string.

    Returns:
        bool: True if the values are acceptable, otherwise False.
    """
    
    json_data = json.loads(request_data.get_data())

    try:
        infra_ok = isinstance(json_data['infraData']['infraID'], str) and len(json_data['infraData']['infraID']) > 0
        node_ok = isinstance(json_data['nodeData']['nodeID'], str) and len(json_data['nodeData']['nodeID']) > 0
        bp_ok = isinstance(json_data['bpData']['bpNum'], int) and json_data['bpData']['bpNum'] > 0

        if infra_ok and node_ok and bp_ok:
            return True
        else:
            return False
    except TypeError:
        return False

def ValidateJSON(request_data):
    """Checks if the given string is a valid JSON string.

    Args:
        request_data (string): A request containing the JSON string.

    Returns:
        bool: True if the string is a valid, False if the string is an invalid JSON.
    """
    try:
        json.loads(request_data.get_data())
    except ValueError:
        return False
    return True

def ValidateNecessaryKeysExists(request_data):
    """Checks if the JSON string contains the necessary keys.

    Args:
        jsonData (string): The JSON string to validate.
    
    Returns:
        bool: True if the necessary keys exist in the JSON string. Otherwise False.
    """

    necessary_data = ({'infraData', 'bpData', 'nodeData'})
    json_data = request_data.get_json()

    ### TO-DO: refactoring
    try:
        # Infrastructure related data
        json_data['infraData']['infraID']
        json_data['infraData']['infraName']

        # Local breakpoint related data
        json_data['bpData']['bpNum']
        json_data['bpData']['bpTag']

        # Node related data
        request_data.remote_addr
        json_data['nodeData']['nodeID']
        json_data['nodeData']['nodeName']
        json_data['nodeData']

        return True
    except KeyError:
        return False

    if necessary_data <= set(json_data):
        if (
            {'infraID', 'infraName'} <= set(json_data['infraData']) and
            {'bpNum'} <= set(json_data['bpData']) and
            {'nodeID', 'nodeName'} <= set(json_data['nodeData'])
        ):
           return True 
        else:
            return False
    else:
        return False