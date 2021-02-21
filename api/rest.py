# Represents REST API functions

from util import logger as mstep_logger
from data import repository as mstep_repo
from controller import controller as mstep_controller
from controller import exectree as mstep_exectree
from flask import  Flask, request, jsonify
import datetime, json, logging

app = Flask(__name__)

#Logger setup
logger = logging.getLogger('rest')
logger.propagate = False
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
formatter = logging.Formatter('*** (%(asctime)s): %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

@app.route('/Collector', methods=['POST'])
def Submit_breakpoint_data(methods=['POST']):
    """API site receiving data from VM endpoints.

    Returns:
        response: A Flask response object with the JSON describing the result.
    """

    # A successful request contains a valid JSON, with necessary keys and value types.
    # The breakpoint also has to be a valid breakpoint (breakpoint number either 1 if this is the first breakpoint, or the next if the node already exists in the infrastructure).
    request_data = request
    valid = True
    curr_time = datetime.datetime.now()

    if Validate_JSON(request_data) == False:
        logger.info('Received INVALID breakpoint data from {}'.format(request.remote_addr))
        valid = False
        return jsonify({'success':False, 'message':'Invalid JSON.', 'code':400}), 400, {'ContentType':'application/json'}
    
    if Validate_necessary_keys_exists(request_data.get_json()) == False:
        logger.info('Received INVALID breakpoint data from {}'.format(request.remote_addr))
        valid = False
        return jsonify({'success':False, 'message':'Missing or invalid JSON values.', 'code':422}), 422, {'ContentType':'application/json'}
    
    if Validate_JSON_value_types(request_data) == False:
        logger.info('Received INVALID breakpoint data from {}'.format(request.remote_addr))
        valid = False
        return jsonify({'success':False, 'message':'Missing or invalid JSON keys and/or values.', 'code':422}), 422, {'ContentType':'application/json'}

    if valid == True:
        # The request is valid and contains the necessary data. Passing JSON to controller.
        result = mstep_controller.Process_breakpoint_data(request_data.remote_addr, request_data.get_json(), curr_time)
        if result[0] == 200:
            logger.info('Received VALID breakpoint data from {}'.format(request.remote_addr))
            mstep_logger.Print_breakpoint_info(request_data)

            # Request processed, check if infrastructure is tracked
            if (mstep_exectree.Is_infrastructure_tracked(request_data.get_json()['infraData']['infraID']) == True):
                # Infrastructure is tracked, process global state and send next collective breakpoint
                node_addedd_result = mstep_exectree.Send_collective_breakpoint(request_data.get_json()['infraData']['infraID'])
                logger.info(node_addedd_result[1])
        else:
            logger.info('Received INVALID breakpoint data from {}'.format(request.remote_addr))
        
        return jsonify({'code':result[0], 'message':result[1], 'success':result[2]}), result[0], {'ContentType':'application/json'}
    else:
        # The request was invalid
        return jsonify({'success':False, 'message':'Invalid JSON, invalid keys or invalid values.', 'code':400}), 400, {'ContentType':'application/json'}

@app.route('/Next/<infraID>/<nodeID>', methods=['GET'])
def Get_step_permission(infraID, nodeID):
    """Gets the permission value for a given node in a given infrastructure.

    Args:
        infraID (string): An infrastructure ID.
        nodeID (string): A node ID.

    Returns:
        JSON: A JSON structure containing 'success' and 'next'. 'next' is True if the node's permission is True, False if the node's permission is False.
    """

    if (mstep_controller.Node_exists(infraID, nodeID) == True):
        if (mstep_controller.Is_node_permission_true(infraID, nodeID) == True):
            return json.dumps({'success':True, 'next':True}), 200, {'ContentType':'application/json'}
        else:
            return json.dumps({'success':True,'next':False}), 204, {'ContentType':'application/json'}
    else:
        return json.dumps({'success':False,'next':False}), 404, {'ContentType':'application/json'}

@app.route('/infrastructures/<infra_id>/<node_id>', methods=['GET'])
def Report_breakpoints_of_a_node(infra_id, node_id):
    """Report the details of a given infrastructure and a given node.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.

    Returns:
        JSON: A JSON structure containing all stored breakpoints of the given node.
    """

    if ((mstep_controller.Infra_exists(infra_id) == True) and (mstep_controller.Node_exists(infra_id, node_id) == True)):
        all_breakpoint_data = mstep_repo.Read_breakpoint(infra_id, node_id)

        breakpoints_dict = {}

        i = 0
        while i < len(all_breakpoint_data):
            key = 'breakpoint{}'.format(i + 1)
            breakpoints_dict[key] = json.loads(all_breakpoint_data[i][4])
            i += 1

        return json.dumps(breakpoints_dict, indent=4)
    else:
        return json.dumps({'success':False,'code':404, 'message':'Given node does not exist in the given infrastructure.'}, indent=4), 404, {'ContentType':'application/json'}

@app.route('/infrastructures/', methods=['GET'])
def List_infrastructures():
    """Lists the currently known and/or maintained infrastructure IDs.

    Returns:
        JSON: A JSON structure containing infrastructure IDs.
    """

    return jsonify(dict(infrastructures=mstep_repo.Read_all_infrastructure_ids()))

@app.route('/infrastructures/<infra_id>', methods=['GET'])
def List_nodes_in_inrastructure(infra_id):
    """Lists the IDs of nodes in a given infrastructure.

    Args:
        infra_id (string): An infrastructure ID.

    Returns:
        JSON: A JSON structure containing the node IDs in a given infrastructure.
    """

    return jsonify(dict(infrastructure=infra_id, nodes=mstep_repo.Read_node_ids_from_infra(infra_id)))

#Helper methods and functions
def Validate_JSON(request_data):
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

def Validate_necessary_keys_exists(json_data):
    """Checks if the JSON string contains the necessary keys.

    Args:
        json_data (string): The JSON string to validate.
    
    Returns:
        bool: True if the necessary keys exist in the JSON string. Otherwise False.
    """

    try:
        # Infrastructure related data
        json_data['infraData']
        json_data['infraData']['infraID']
        json_data['infraData']['infraName']

        # Local breakpoint related data
        json_data['bpData']
        json_data['bpData']['bpTag']

        # Node related data
        json_data['nodeData']
        json_data['nodeData']['nodeID']
        json_data['nodeData']['nodeName']
        json_data['nodeData']['nodeIP']

    except KeyError:
        return False
    return True

def Validate_JSON_value_types(request_data):
    """Validates if the necessary keys have proper value types.

    Args:
        request_data (request): A request containing the JSON string.

    Returns:
        bool: True if the values are acceptable, otherwise False.
    """
    
    json_data = json.loads(request_data.get_data())

    try:
        infra_ok = ((isinstance(json_data['infraData']['infraID'], str)) and (len(json_data['infraData']['infraID']) > 0))
        infra_ok = infra_ok and ((isinstance(json_data['infraData']['infraName'], str)) and (len(json_data['infraData']['infraName']) > 0))

        bp_ok = (isinstance(json_data['bpData']['bpTag'], str))

        node_ok = ((isinstance(json_data['nodeData']['nodeID'], str)) and (len(json_data['nodeData']['nodeID']) > 0))
        node_ok = node_ok and ((isinstance(json_data['nodeData']['nodeName'], str)) and (len(json_data['nodeData']['nodeName']) > 0))
        node_ok = node_ok and ((isinstance(json_data['nodeData']['nodeIP'], str)) and (len(json_data['nodeData']['nodeIP']) > 0))

        if (infra_ok and node_ok and bp_ok) == True:
            return True
    except TypeError:
        return False
    except ValueError:
        return False
    return False