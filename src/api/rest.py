# Represents REST API functions

from controller import controller as mstepcontroller
from controller import neo4j_handler as mstepneo4j_handler
from flask import Flask, request, jsonify
import datetime, json

app = Flask(__name__)

@app.route('/MSTEP_API/Collector', methods=['POST'])
def APIdatacollector():
    """API site receiving data from VM endpoints.

    Returns:
        response: A Flask response object with the JSON describing the result.
    """

    request_data = request

    # A successful request contains a valid JSON, with necessary keys and values. The breakpoint also has to be a valid breakpoint (breakpoint number either 1 if this is 
    # the first breakpoint, or the next if the node already exists in the infrastructure).
    valid = ValidateJSON(request_data)

    if valid == False:
        PrintConsoleInvalidData()
        return jsonify({'success':False, 'message':'Invalid JSON.', 'code':400}), 400, {'ContentType':'application/json'}
    else:
        valid = valid and ValidateNecessaryKeysExists(request_data.get_json())

        if valid == False:
            PrintConsoleInvalidData()
            return jsonify({'success':False, 'message':'Missing or invalid JSON keys and/or values.', 'code':422}), 422, {'ContentType':'application/json'}
        else:
            valid = valid and ValidateJSONValues(request_data)

            if valid == False or valid == None:
                PrintConsoleInvalidData()
                return jsonify({'success':False, 'message':'Missing or invalid JSON values.', 'code':422}), 422, {'ContentType':'application/json'}

    if valid == True:
        # The request is valid and contains the necessary data. Passing JSON to controller.          
        result = mstepcontroller.ProcessJSON(request_data.remote_addr, request_data.get_json())
        if result[0] == 200:
            PrintConsoleRequestData(request_data)

            # Request processed, check if infrastructure is tracked
            if (mstepneo4j_handler.IsInfraTracked(request_data.get_json()['infraData']['infraID'])):
                # Infrastructure is tracked, process global state and send next collective breakpoint
                mstepneo4j_handler.SendCollectiveBreakpoint(request_data.get_json()['infraData']['infraID'])
        else:
            PrintConsoleInvalidData()

        return jsonify({'code':result[0], 'message':result[1], 'success':result[2]}), result[0], {'ContentType':'application/json'}
    else:
        # The request was invalid
        PrintConsoleInvalidData()
        return jsonify({'success':False, 'message':'Invalid JSON, invalid keys or invalid values.', 'code':400}), 400, {'ContentType':'application/json'}

@app.route("/MSTEP_API/Next/<infraID>/<nodeID>", methods=['GET'])
def GetMoveToNextBP(infraID, nodeID):
    
    # Check if infra and node exists, also if the node can move to the next breakpoint
    if mstepcontroller.InfraExists(infraID) == True and mstepcontroller.NodeExists(infraID, nodeID) == True and mstepcontroller.CanNodeMoveNext(infraID, nodeID) == True:
        return json.dumps({'success':True, 'next':True}), 200, {'ContentType':'application/json'}
    else:
        return json.dumps({'success':False,'next':False}), 204, {'ContentType':'application/json'}

@app.route("/MSTEP_API/<infraID>", methods=['GET'])
def GetInfrastructureData(infraID):
    return "Not implemented yet."

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
        infra_ok = infra_ok and isinstance(json_data['infraData']['infraName'], str) and len(json_data['infraData']['infraName']) > 0

        node_ok = isinstance(json_data['nodeData']['nodeID'], str) and len(json_data['nodeData']['nodeID']) > 0
        node_ok = node_ok and isinstance(json_data['nodeData']['nodeName'], str) and len(json_data['nodeData']['nodeName']) > 0
        node_ok = node_ok and isinstance(json_data['nodeData']['nodeIP'], str) and len(json_data['nodeData']['nodeIP']) > 0

        bp_ok = isinstance(json_data['bpData']['bpNum'], int) and json_data['bpData']['bpNum'] > 0
        
        if isinstance(json_data['bpData']['bpNum'], bool):
            raise ValueError

        bp_ok = bp_ok and isinstance(json_data['bpData']['bpTag'], str)

        if infra_ok and node_ok and bp_ok:
            return True
    except TypeError:
        return False
    except ValueError:
        return False

def ValidateJSON(request_data):
    """Checks if the given string is a valid JSON string.

    Args:
        request_data (request): A request containing the JSON to validate.

    Returns:
        bool: True if the string is a valid, False if the string is an invalid JSON.
    """
    try:
        json.loads(request_data.get_data())
    except ValueError:
        return False
    return True

def ValidateNecessaryKeysExists(json_data):
    """Checks if the JSON string contains the necessary keys.

    Args:
        json_data (string): The JSON string to validate.
    
    Returns:
        bool: True if the necessary keys exist in the JSON string. Otherwise False.
    """

    necessary_data = ({'infraData', 'bpData', 'nodeData'})

    try:
        # Infrastructure related data
        json_data['infraData']['infraID']
        json_data['infraData']['infraName']

        # Local breakpoint related data
        json_data['bpData']['bpNum']
        json_data['bpData']['bpTag']

        # Node related data
        json_data['nodeData']['nodeID']
        json_data['nodeData']['nodeName']
        json_data['nodeData']['nodeIP']
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

def PrintConsoleInvalidData():
    """Prints a message stating the received data were invalid.
    """
    print('\r\n*** ({}) Received INVALID breakpoint data.'.format(datetime.datetime.now().strftime('%Y.%m.%d. %H:%M:%S.%f')[:-3]))

def PrintConsoleRequestData(request_data):
    """Prints the received VM data to the console.

    Args:
        request_data (request): A request containing a JSON string.
    """

    json_data = request_data.get_json()
 
    # Infrastructure related data
    infra_id = json_data['infraData']['infraID']
    infra_name = json_data['infraData']['infraName']

    # Local breakpoint related data
    bp_id = json_data['bpData']['bpNum']
    bp_tag = json_data['bpData']['bpTag']

    # Node related data
    node_publicIP = request_data.remote_addr
    node_id = json_data['nodeData']['nodeID']
    node_name = json_data['nodeData']['nodeName']
    node_data = json_data['nodeData']

    # Printing received information
    print('\r\n*** ({}) Received VALID breakpoint data.'.format(datetime.datetime.now().strftime('%Y.%m.%d. %H:%M:%S.%f')[:-3]))

    print('*** From infrastructure with ID: {}'.format(infra_id))
    print('*** From infrastructure with Name: {}'.format(infra_name))

    print('*** From node with ID: {}'.format(node_id))
    print('*** From node with Name: {}'.format(node_name))

    print('*** Local breakpoint Number: {}'.format(bp_id))
    print('*** Local breakpoint description: {}'.format(bp_tag))

    print('*** Node Data:')

    for dataKey in node_data:
        print('*** {}: {}'.format(dataKey, node_data[dataKey]))

    print('*** nodePublicIP: {}\r\n'.format(node_publicIP))