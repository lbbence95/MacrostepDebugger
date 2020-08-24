# Represents API functions

from flask import Flask, request, jsonify

import json

import src.util.consolelogs as mstep_conlogger
import src.controller.controller as mstepcontroller

app = Flask(__name__)

@app.route('/MSTEP_API/Collector', methods=['POST'])
def APIdatacollector():
    """API site receiving data from VM endpoints.

    Returns:
        string: An HTTP response with a JSON string describing the result.
    """

    request_data = request

    # A successful request contains a valid JSON, with necessary keys and values. The breakpoint also has to be a valid breakpoint (breakpoint number either 1 if this is 
    # the first breakpoint, or the next if the node already exists in the infrastructure).

    valid = ValidateJSON(request_data)

    if valid == False:
        mstep_conlogger.PrintConsoleInvalidData()
        return jsonify({'success':False, 'message':'Invalid JSON.', 'code':400}), 400, {'ContentType':'application/json'}
    else:
        valid = valid and ValidateNecessaryKeysExists(request_data.get_json())

        if valid == False:
            mstep_conlogger.PrintConsoleInvalidData()
            return jsonify({'success':False, 'message':'Missing or invalid JSON keys and/or values.', 'code':422}), 422, {'ContentType':'application/json'}
        else:
            valid = valid and ValidateJSONValues(request_data)

            if valid == False:
                # TO-DO: valid (may) becomes None. Why?
                mstep_conlogger.PrintConsoleInvalidData()
                return jsonify({'success':False, 'message':'Missing or invalid JSON values.', 'code':422}), 422, {'ContentType':'application/json'}

    if valid == True:
        # The request is valid and contains the necessary data. Passing JSON to controller.          
        result = mstepcontroller.ProcessJSON(request_data.remote_addr, request_data.get_json())
        if result[0] == 200:
            mstep_conlogger.PrintConsoleRequestData(request_data) 
        else:
            mstep_conlogger.PrintConsoleInvalidData()

        return jsonify({'code':result[0], 'message':result[1], 'success':result[2]}), result[0], {'ContentType':'application/json'}
    else:
        # The request was invalid
        mstep_conlogger.PrintConsoleInvalidData()
        return jsonify({'success':False, 'message':'Invalid JSON, invalid keys or invalid values.', 'code':400}), 400, {'ContentType':'application/json'}

@app.route("/MSTEP_API/Next/<infraID>/<nodeID>", methods=['GET'])
def GetMoveToNextBP(infraID, nodeID):
    
    # Check if infra and node exist, if the node can move to the next breakpoint
    if mstepcontroller.InfraExists(infraID) == True and mstepcontroller.NodeExists(infraID, nodeID) == True and mstepcontroller.CanNodeMoveNext(infraID, nodeID) == True:
        return json.dumps({'success':True, 'next':True}), 200, {'ContentType':'application/json'}
    else:
        return json.dumps({'success':False,'next':False}), 204, {'ContentType':'application/json'}

@app.route("/MSTEP_API/<infraID>", methods=['GET'])
def GetInfrastructureData(infraID):
    pass

# TEST - TO-DO
# Stopping the service without a route
#def Stop():
#    func = request.environ.get('werkzeug.server.shutdown')
#    if func is None:
#        raise RuntimeError('Not running with the Werkzeug Server')
#    func()
#    pass

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

    ### TO-DO: refactoring, (maybe one-level JSON, not two-level JSON ?)
    try:
        # Infrastructure related data
        json_data['infraData']['infraID']
        json_data['infraData']['infraName']

        # Local breakpoint related data
        json_data['bpData']['bpNum']
        json_data['bpData']['bpTag']

        # Node related data
        # request_data.remote_addr
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