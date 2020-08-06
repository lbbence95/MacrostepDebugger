# Contains validation functions.


import json


def ValidateJSONValues(request_data):
    
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

    #infra_ok = isinstance(json_data['infraData']['infraID'], str) and len(json_data['infraData']['infraID']) > 0
    #node_ok = isinstance(json_data['nodeData']['nodeID'], str) and len(json_data['nodeData']['nodeID']) > 0
    #bp_ok = isinstance(json_data['bpData']['bpNum'], int) and json_data['bpData']['bpNum'] > 0

    #if infra_ok and node_ok and bp_ok:
    #    return True
    #else:
    #    return False


def ValidateJSON(request_data):
    """Checks if the given string is a valid JSON string.

    Args:
        jsonData (string): A string to validate.

    Returns:
        bool: True if the string is a valid, False if the string is an invalid JSON.
    """
    try:
        json.loads(request_data.get_data())
    except ValueError:
        
        # The sent JSON string is invalid
        return False
    return True


def ValidateNecessaryKeysExists(request_data):
    """Checks if the JSON string contains the necessary keys.

    Args:
        jsonData (string): The JSON string to validate.
    
    Returns:
        bool: True if the necessary keys exist in the JSON string. Otherwise False.
    """

    necessaryData = ({'infraData', 'bpData', 'nodeData'})
    jsonData = request_data.get_json()

    if necessaryData <= set(jsonData):
        if (
            {'infraID', 'infraName'} <= set(jsonData['infraData']) and
            {'bpNum'} <= set(jsonData['bpData']) and
            {'nodeID', 'nodeName'} <= set(jsonData['nodeData'])
        ):
           return True 
        else:
            return False
    else:
        return False