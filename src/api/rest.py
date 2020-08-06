# Represents API and CLI functions

from flask import Flask, request, jsonify
from datetime import datetime

import json

import src.util.consolelogs as mstep_conlogger
import src.util.validation as mstepvalidation
import src.controller.controller as mstepcontroller


app = Flask(__name__)
mstepcontroller.InitializeDB()


@app.route('/MSTEP_API/Collector', methods=['POST'])
def APIdatacollector():
    """API site receiving data from VM endpoints.

    Returns:
        string: An HTTP response with a JSON string describing the result.
    """

    request_data = request

    infraID = request_data.get_json()['infraData']['infraID']
    nodeID = request_data.get_json()['nodeData']['nodeID']
    bpid = int(json.dumps(request_data.get_json()['bpData']['bpNum']))

    # Check if the request contains the necessary data in the necessary format.
    successful = mstepvalidation.ValidateJSON(request_data) and mstepvalidation.ValidateNecessaryKeysExists(request_data) and mstepvalidation.ValidateJSONValues(request_data)

    # Check if the node exists
    if mstepcontroller.NodeExists(infraID, nodeID) == True:

        # It does exist, check if its a valid next breakpoint.
        successful = successful and mstepcontroller.IsNewBreakpointNext(infraID, nodeID, bpid)
    else:

        # It does not exist, therefore check if the breakpoint is 1
        successful = successful and (bpid == 1)

    # A successful request contains a valid JSON, with necessary keys and values. The breakpoint also has to be a valid breakpoint (breakpoint number either 1 if this is 
    # the first breakpoint, or N if the node already exists in the infrastructure.
    if successful == True:

        # The request is valid and contains the necessary data.

        mstep_conlogger.PrintConsoleRequestData(request_data)

        infraName = request_data.get_json()['infraData']['infraName']     
        nodeName = request_data.get_json()['nodeData']['nodeName']

        if mstepcontroller.InfraExists(infraID) == False:

            # Register the new infrastructure and the new node, along with the new breakpoint.
                       
            mstepcontroller.RegisterInfrastructure(infraID, infraName, datetime.now().strftime('%H:%M:%S.%f')[:-3])
            mstepcontroller.RegisterNode(infraID, nodeID, nodeName, datetime.now().strftime('%H:%M:%S.%f')[:-3], int(json.dumps(request_data.get_json()['bpData']['bpNum'])))
            mstepcontroller.RegisterBreakpoint(infraID, nodeID, datetime.now().strftime('%H:%M:%S.%f')[:-3], bpid, str(request_data.get_json()))

            print("*** New infrastructure added!")
            print("*** New node added!")
            print("*** New breakpoint added!")

            # Test
            mstep_conlogger.PrintManagedInfras()
            mstep_conlogger.PrintManagedNodes()
            mstep_conlogger.PrintBreakpoints()

        else:
            if mstepcontroller.NodeExists(infraID, nodeID) == False:
            
                # The infrastructure exists, but the new node does not. Register it and the new BP.

                mstepcontroller.RegisterNode(infraID, nodeID, nodeName, datetime.now().strftime('%H:%M:%S.%f')[:-3], int(json.dumps(request_data.get_json()['bpData']['bpNum'])))
                mstepcontroller.RegisterBreakpoint(infraID, nodeID, datetime.now().strftime('%H:%M:%S.%f')[:-3], bpid, str(request_data.get_json()))

                print("*** New node added!")
                print("*** New breakpoint added!")

                # Test
                mstep_conlogger.PrintManagedInfras()
                mstep_conlogger.PrintManagedNodes()
                mstep_conlogger.PrintBreakpoints()
            else:

                # The infrastructure exists, the node exists. Check if this is a new breakpoint.
                # Register the new BP, and update the node to the retreived BP ID. Otherwise return invalid request.

                if (mstepcontroller.IsNewBreakpointNext(infraID, nodeID, bpid) == True):

                    mstepcontroller.UpdateNodeBreakpoint(infraID, nodeID)
                    mstepcontroller.RegisterBreakpoint(infraID, nodeID, datetime.now().strftime('%H:%M:%S.%f')[:-3], bpid, str(request_data.get_json()))

                    print("*** New breakpoint added!")

                    # Test
                    mstep_conlogger.PrintManagedInfras()
                    mstep_conlogger.PrintManagedNodes()
                    mstep_conlogger.PrintBreakpoints()

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
    """Returns whether the given node can move to the next breakpoint or not.

    Args:
        infraID (string): An infrastructure ID.
        nodeID (string): A node ID.
    """
    return ""