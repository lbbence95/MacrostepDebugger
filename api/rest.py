# Represents REST API functions

from util import logger as mstep_logger
from data import repository as mstep_repo
from flask import  Flask, request, jsonify
from datetime import datetime
import json, logging

app = Flask(__name__)

#Logger setup
logger = logging.getLogger('rest')
logger.propagate = False
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
formatter = logging.Formatter('*** (%(asctime)s): %(message)s', "%Y-%m-%d %H:%M:%S")
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)


@app.route('/Submit/<infra_id>/<node_id>/', methods=['POST'])
def Submit_breakpoint_data(infra_id, node_id):
    """API endpoint receiving data from VM endpoints.

    Returns:
        response: A Flask response object with JSON describing the result.
    """

    # A successful request contains valid JSON content, with the necessary keys and value types.
    # The breakpoint also has to be a valid breakpoint (breakpoint number either 1 if this is the first breakpoint, or the next if the node already exists in the infrastructure).
    request_data = request
    valid = True
    curr_time = datetime.now()

    if (mstep_repo.Infra_exists(infra_id) == False):
        logger.info('Received INVALID breakpoint data from {}. No such infrastructure.'.format(request.remote_addr))
        valid = False
        return jsonify({'success':False, 'message':'No infrastructure exists with this ID.', 'code':404}), 404, {'ContentType':'application/json'}

    if (Validate_JSON(request_data) == False):
        logger.info('Received INVALID breakpoint data from {}. Invalid JSON.'.format(request.remote_addr))
        valid = False
        return jsonify({'success':False, 'message':'Invalid JSON.', 'code':400}), 400, {'ContentType':'application/json'}
    
    if (Validate_necessary_keys_exists(request_data.get_json()) == False):
        logger.info('Received INVALID breakpoint data from {}. Missing or invalid JSON values.'.format(request.remote_addr))
        valid = False
        return jsonify({'success':False, 'message':'Missing or invalid values.', 'code':422}), 422, {'ContentType':'application/json'}
    
    if (Validate_JSON_value_types(request_data) == False):
        logger.info('Received INVALID breakpoint data from {}. Missing or invalid keys.'.format(request.remote_addr))
        valid = False
        return jsonify({'success':False, 'message':'Missing or invalid JSON keys and/or values.', 'code':422}), 422, {'ContentType':'application/json'}

    if (valid == True):
        # The request is valid and contains the necessary data.
        result = Process_breakpoint_data(request_data.remote_addr, request_data.get_json(), curr_time)

        if (result[0] == 200):
            logger.info('Received VALID breakpoint data from {}'.format(request.remote_addr))
            mstep_logger.Print_breakpoint_info(request_data)
        else:
            logger.info('Received INVALID breakpoint data from {}'.format(request.remote_addr))
        
        return jsonify({'code':result[0], 'message':result[1], 'success':result[2]}), result[0], {'ContentType':'application/json'}
    else:
        # The request was invalid
        print('\r\n\n\n{}\r\n\n'.format(request_data.get_json()))
        return jsonify({'success':False, 'message':'Invalid JSON, invalid keys or invalid values.', 'code':400}), 400, {'ContentType':'application/json'}


@app.route('/Next/<infraID>/<nodeID>/', methods=['GET'])
def Get_step_permission(infraID, nodeID):
    """Gets the permission value for a given node in a given infrastructure.

    Args:
        infraID (string): An infrastructure ID.
        nodeID (string): A node ID.

    Returns:
        JSON: A JSON structure containing 'success' and 'next'. 'next' is True if the node's permission is True, False if the node's permission is False.
    """

    if (mstep_repo.Node_exists(infraID, nodeID) == True):
        if (mstep_repo.Is_node_permission_true(infraID, nodeID) == True):
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

    if ((mstep_repo.Infra_exists(infra_id) == True) and (mstep_repo.Node_exists(infra_id, node_id) == True)):
        all_breakpoint_data = mstep_repo.Read_given_nodes_breakpoint(infra_id, node_id)

        breakpoints_dict = {}

        i = 0
        while (i < len(all_breakpoint_data)):
            key = 'breakpoint{}'.format(i + 1)
            breakpoints_dict[key] = json.loads(all_breakpoint_data[i].bp_data)
            i += 1

        return json.dumps(breakpoints_dict, indent=2)
    else:
        return json.dumps({'success':False,'code':404, 'message':'Given node does not exist in the given infrastructure.'}, indent=4), 404, {'ContentType':'application/json'}

@app.route('/infrastructures/', methods=['GET'])
def List_infrastructures():
    """Lists the currently known and/or maintained infrastructure IDs.

    Returns:
        JSON: A JSON structure containing infrastructure IDs.
    """

    return "200"

@app.route('/infrastructures/<infra_id>', methods=['GET'])
def List_nodes_in_inrastructure(infra_id):
    """Lists the IDs of nodes in a given infrastructure.

    Args:
        infra_id (string): An infrastructure ID.

    Returns:
        JSON: A JSON structure containing the node IDs in a given infrastructure.
    """

    return "200"

#Helper methods and functions
def Process_breakpoint_data(public_ip, json_data, curr_time):
    """Processes a JSON string and a public IP address

    Args:
        public_ip (string): An IP adress.
        json_data (string): A JSON string.
        curr_time (datetime): The datetime the breakpoint data was received.

    Returns:
        tuple: Contains a status code, a description message, and a success indicator.
    """
    
    curr_time = curr_time.strftime('%Y.%m.%d. %H:%M:%S.%f')[:-3]
    infra_name = json_data['processData']['infraName']
    infra_id = json_data['processData']['infraID']
    node_name = json_data['processData']['nodeName']
    node_id = json_data['processData']['nodeID']
    bp_tag = json_data['processData']['bpTag']

    bp_id = 1

    #Check if infrastructure already exists.
    if (mstep_repo.Infra_exists(infra_id) == False):
        #Infrastucture does not exist, first breakpoint. Update the infrastructure. Register the node, and the breakpoint.
        mstep_repo.Update_infrastructure_name(infra_id, infra_name)
        mstep_repo.Register_new_node(infra_id, node_id, node_name, datetime.now(), bp_id, public_ip)
        mstep_repo.Register_new_breakpoint(infra_id, node_id, datetime.now(), int(bp_id), json.dumps(json_data), bp_tag)

        logger.info('New infrastructure added!')
        logger.info('New node added!')
        logger.info('New breakpoint added!')

        return (200, 'Valid JSON. New infrastructure, node and breakpoint added.', True)
    else:
        #Infrastructure exists, check if node already exists.
        if (mstep_repo.Node_exists(infra_id,node_id) == False):
            #Node does not exist, store new node and breakpoint.
            mstep_repo.Register_new_node(infra_id, node_id, node_name, datetime.now(), bp_id, public_ip)
            mstep_repo.Register_new_breakpoint(infra_id, node_id, datetime.now(), int(bp_id), json.dumps(json_data), bp_tag)

            logger.info('New node added!')
            logger.info('New breakpoint added!')

            read_infra_name = mstep_repo.Read_given_infrastructure(infra_id).infra_name
            print(read_infra_name)

            if (read_infra_name == ""):
                mstep_repo.Update_infrastructure_name(infra_id, infra_name)
                logger.info('Infrastructure updated!')

            return (200, 'Valid JSON. New node and breakpoint added.', True)
        else:
            #Node exists, store new breakpoint data. Update node breakpoint ID.            
            bp_id = (mstep_repo.Read_current_bp_num_for_node(infra_id, node_id)) + 1

            mstep_repo.Register_new_breakpoint(infra_id, node_id, datetime.now(), int(bp_id), json.dumps(json_data), bp_tag)
            mstep_repo.Update_node_current_bp_and_permission(infra_id, node_id)
			
            tags = bp_tag.split(' ')

            if (any((True for x in ['last', 'last_bp'] if x in tags)) == True):
                mstep_repo.Update_node_status_finished(infra_id, node_id)
                logger.info('"{}/{}" reached its last breakpoint.'.format(infra_id, node_id))

            logger.info('New breakpoint added!')
            logger.info('Node updated!')
            return (200, 'Valid JSON. New breakpoint added, node status updated.', True)

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
        json_data['processData']
        json_data['processData']['infraID']
        json_data['processData']['infraName']
        json_data['processData']['nodeID']
        json_data['processData']['nodeName']
        json_data['processData']['bpTag']

        json_data['userData']
        json_data['userData']['nodeIP']

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
        infra_ok = ((isinstance(json_data['processData']['infraID'], str)) and (len(json_data['processData']['infraID']) > 0))
        infra_ok = infra_ok and ((isinstance(json_data['processData']['infraName'], str)) and (len(json_data['processData']['infraName']) > 0))

        bp_ok = (isinstance(json_data['processData']['bpTag'], str))

        node_ok = ((isinstance(json_data['processData']['nodeID'], str)) and (len(json_data['processData']['nodeID']) > 0))
        node_ok = node_ok and ((isinstance(json_data['processData']['nodeName'], str)) and (len(json_data['processData']['nodeName']) > 0))
        node_ok = node_ok and ((isinstance(json_data['userData']['nodeIP'], str)) and (len(json_data['userData']['nodeIP']) > 0))

        if (infra_ok and node_ok and bp_ok) == True:
            return True
    except TypeError:
        return False
    except ValueError:
        return False
    return False