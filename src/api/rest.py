# Represents API functions

from flask import Flask, request, jsonify
from datetime import datetime

import json

import src.util.consolelogs as mstep_conlogger
import src.controller.controller as mstepcontroller

app = Flask(__name__)

def Init():
    """Initializes the application.
    """
    mstepcontroller.InitializeDB()

@app.route('/MSTEP_API/Collector', methods=['POST'])
def APIdatacollector():
    """API site receiving data from VM endpoints.

    Returns:
        string: An HTTP response with a JSON string describing the result.
    """

    request_data = request

    # A successful request contains a valid JSON, with necessary keys and values. The breakpoint also has to be a valid breakpoint (breakpoint number either 1 if this is 
    # the first breakpoint, or the next if the node already exists in the infrastructure).
    successful = ValidateJSON(request_data) and ValidateNecessaryKeysExists(request_data) and ValidateJSONValues(request_data)

    infra_id, node_id, bp_id = None, None, None

    ### TO-DO: refactoring, move JSON handling to controller
    ### TO-DO: API should only validate requests then forward it to the controller
    if successful == True:
        infra_id = request_data.get_json()['infraData']['infraID']
        node_id = request_data.get_json()['nodeData']['nodeID']
        bp_id = int(json.dumps(request_data.get_json()['bpData']['bpNum']))
    else:
        mstep_conlogger.PrintConsoleInvalidData()
        return jsonify({'success':False, 'validJSON':False, 'description':'JSON is invalid'}), 400

    # Check if the node exists
    if mstepcontroller.NodeExists(infra_id, node_id) == True:
        # It does exist, check if its a valid next breakpoint.
        successful = successful and mstepcontroller.IsNewBreakpointNext(infra_id, node_id, bp_id)
    else:
        # It does not exist, check if the breakpoint is 1
        successful = successful and (bp_id == 1)

    if successful == True:

        # The request is valid and contains the necessary data.
        mstep_conlogger.PrintConsoleRequestData(request_data)

        infraName = request_data.get_json()['infraData']['infraName']     
        nodeName = request_data.get_json()['nodeData']['nodeName']
        bp_tag = request_data.get_json()['bpData']['bpTag']

        if mstepcontroller.InfraExists(infra_id) == False:

            # Register the new infrastructure and the new node, along with the new breakpoint.                  
            mstepcontroller.RegisterInfrastructure(infra_id, infraName, datetime.now().strftime('%H:%M:%S.%f')[:-3])
            mstepcontroller.RegisterNode(infra_id, node_id, nodeName, datetime.now().strftime('%H:%M:%S.%f')[:-3], int(json.dumps(request_data.get_json()['bpData']['bpNum'])), request_data.remote_addr)
            mstepcontroller.RegisterBreakpoint(infra_id, node_id, datetime.now().strftime('%H:%M:%S.%f')[:-3], bp_id, str(request_data.get_json()), bp_tag)

            print("*** New infrastructure added!")
            print("*** New node added!")
            print("*** New breakpoint added!")

            # Test
            # mstep_conlogger.PrintManagedInfras()
            # mstep_conlogger.PrintManagedNodes()
            # mstep_conlogger.PrintBreakpoints()

        else:
            if mstepcontroller.NodeExists(infra_id, node_id) == False:
            
                # The infrastructure exists, but the new node does not. Register it and the new BP.

                mstepcontroller.RegisterNode(infra_id, node_id, nodeName, datetime.now().strftime('%H:%M:%S.%f')[:-3], int(json.dumps(request_data.get_json()['bpData']['bpNum'])), request_data.remote_addr)
                mstepcontroller.RegisterBreakpoint(infra_id, node_id, datetime.now().strftime('%H:%M:%S.%f')[:-3], bp_id, str(request_data.get_json()), bp_tag)

                print("*** New node added!")
                print("*** New breakpoint added!")

                # Test
                # mstep_conlogger.PrintManagedInfras()
                #mstep_conlogger.PrintManagedNodes()
                # mstep_conlogger.PrintBreakpoints()
            else:

                # The infrastructure exists, the node exists. Check if this is a new breakpoint.
                # Register the new BP, and update the node to the retreived BP ID. Otherwise return invalid request.

                if (mstepcontroller.IsNewBreakpointNext(infra_id, node_id, bp_id) == True):

                    mstepcontroller.UpdateNodeBreakpoint(infra_id, node_id)
                    mstepcontroller.RegisterBreakpoint(infra_id, node_id, datetime.now().strftime('%H:%M:%S.%f')[:-3], bp_id, str(request_data.get_json()), bp_tag)

                    print("*** New breakpoint added!")

                    # Test
                    # mstep_conlogger.PrintManagedInfras()
                    # mstep_conlogger.PrintManagedNodes()
                    # mstep_conlogger.PrintBreakpoints()

                else:
                    mstep_conlogger.PrintConsoleInvalidData()

                    return jsonify({'success':False, 'validJSON':False, 'description':'JSON is invalid'}), 400

        return jsonify({'success':True, 'validJSON':True, 'description':'JSON is valid'}), 200
        # Alternative: return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
    else:

        # The request was invalid

        mstep_conlogger.PrintConsoleInvalidData()

        return jsonify({'success':False, 'validJSON':False, 'description':'JSON is invalid'}), 400

@app.route("/MSTEP_API/Next/<infraID>/<nodeID>", methods=['GET'])
def GetMoveToNextBP(infraID, nodeID):
    
    # Check if infra and node exist and if the node can move to the next breakpoint
    if mstepcontroller.InfraExists(infraID) == True and mstepcontroller.NodeExists(infraID, nodeID) == True and mstepcontroller.CanNodeMoveNext(infraID, nodeID):
        return json.dumps({'success':True, 'next':True}), 200, {'ContentType':'application/json'}
    else:
        # 204 - No Content
        return json.dumps({'success':False,'next':False}), 204, {'ContentType':'application/json'}

    return ""

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