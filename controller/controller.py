# Represents the controller module of the debugger

from data import repository as mstep_repo
from util import logger as mstep_logger
from controller import exectree as mstep_exectree
from time import strftime
import datetime, json, os.path, logging, requests, time

#Logger setup
logger = logging.getLogger('controller')
logger.propagate = False
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
formatter = logging.Formatter('*** (%(asctime)s): %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def Initialize():
    """Initializes a new database.
    """

    if os.path.exists("data/mstepDB.db"):
        logger.info('Local database: exists.')
    else:
        logger.warning('Local database: does not exist.')
        mstep_repo.Initialize_db()

def Clear_database():
    """Clears the current database.
    """
    mstep_repo.Initialize_db()

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
    infra_name = json_data['infraData']['infraName']
    infra_id = json_data['infraData']['infraID']
    node_name = json_data['nodeData']['nodeName']
    node_id = json_data['nodeData']['nodeID']
    bp_tag = json_data['bpData']['bpTag']

    #Initial breakpoint ID.
    bp_id = 1

    #Check if infrastructure already exists.
    if (Infra_exists(infra_id) == False):
        #Infrastucture does not exist, first breakpoint. Register the infrastructure, the node, and the breakpoint.
        mstep_repo.Register_infrastructure(infra_id, infra_name, curr_time)
        mstep_repo.Register_node(infra_id, node_id, node_name, curr_time, bp_id, public_ip)
        mstep_repo.Register_breakpoint(infra_id, node_id, curr_time, int(bp_id), json.dumps(json_data), bp_tag)

        logger.info('New infrastructure added!')
        logger.info('New node added!')
        logger.info('New breakpoint added!')

        return (200, 'Valid JSON. New infrastructure, node and breakpoint added.', True)
    else:
        #Infrastructure exists, check if node already exists.
        if (Node_exists(infra_id,node_id) == False):
            #Node does not exist, store new node and breakpoint.
            mstep_repo.Register_node(infra_id, node_id, node_name, curr_time, bp_id, public_ip)
            mstep_repo.Register_breakpoint(infra_id, node_id, curr_time, int(bp_id), json.dumps(json_data), bp_tag)

            logger.info('New node added!')
            logger.info('New breakpoint added!')

            return (200, 'Valid JSON. New node and breakpoint added.', True)
        else:
            #Node exists, store new breakpoint data. Update node breakpoint ID.
            bp_id = (mstep_repo.Get_bp_id_for_node(infra_id, node_id)) + 1

            mstep_repo.Register_breakpoint(infra_id, node_id, curr_time, int(bp_id), json.dumps(json_data), bp_tag)
            mstep_repo.Update_node_at_breakpoint(infra_id, node_id)

            logger.info('New breakpoint added!')
            logger.info('Node updated!')
            return (200, 'Valid JSON. New breakpoint added, node status updated.', True)

def Step_whole_infra(infra_id):
    """Permits all nodes in the given infrastructure to move to the next breakpoint.

    Args:
        infra_id (string): An infrastructure ID.
    """

    infra_nodes = mstep_repo.Read_nodes_from_infra(infra_id)

    for act_node in infra_nodes:
        mstep_repo.Update_node_step_permission(infra_id, act_node[1])

def Step_given_nodes(infra_id, nodes):
    """Permits the given node to move to the next breakpoint.

    Args:
       infra_id (string): An infrastructure ID.
       nodes (list): A list of node IDs.
    """

    for act_node in nodes:
        if (Node_exists(infra_id, act_node) == True):
            mstep_repo.Update_node_step_permission(infra_id, act_node)

def Replay_infrastructure_to_state_Occo(application, state, infra_file, orch_url):
    """Replays a given appication to the given unique state.

    Args:
        application (string): An application name.
        state (string): A collective breakpoint ID that identifies a unique state in the exectuion tree.
        infra_file (string): The path to the infrastructure description file to be used by the Occopus cloud-orchestrator.
        orch_url (string): An URL where Occopus is available.
    """

    #Get and check database connection
    conn_details = mstep_exectree.Read_connection_details()
    
    if (conn_details[0] == False):
        #Connection error
        logger.warning('Please check Neo4j configuration file.')
    else:
        #Connection OK
        #Check if given collective breakpoint in the application exists.
        path_exists = mstep_exectree.Get_path_to_target_coll_bp(application, state, conn_details[1])
        path_collective_bps = path_exists[0]
        path_states = path_exists[1]

        if (path_collective_bps == None):
            #No such collective breakpoint
            logger.info('No collective breakpoint exists with ID "{}" in application "{}".'.format(state, application))
        else:
            #Given collective breakpoint exists. Get the execution path to the given state.
            target_state = path_states[-1]

            #Print targeted state and path
            logger.info('Collective breakpoint found! Targeted global state: {}'.format(target_state))
            logger.info('Global states on path: {}'.format(path_states))
            print()
            logger.info('Path collective breakpoints: {}'.format(path_collective_bps))
            print()

            #Create an infrastructure instance
            orch_url = orch_url
            app_file = open(infra_file, 'rb')
            response = requests.post(url=orch_url, data=app_file)
            instance_infra_id = response.json()['infraid']

            print('*** Instance ID: {}'.format(instance_infra_id))

            if (response.status_code == 200):
                #Succes, proceed with replay
                instance_index_next = 0
                instance_next_desired_state = path_states[instance_index_next]
                instance_curr_state = 'init'

                logger.info('Instance current state: initializing.')

                #Replay shall proceed until desired state is reached
                while (instance_curr_state != target_state):
                    # Check for consistent global state
                    if ((mstep_exectree.Is_consistent_global_state(instance_infra_id) == True) and (json.dumps(mstep_exectree.Get_node_states(instance_infra_id)) == instance_next_desired_state)):
                        # Global state is consistent and the next desired global state
                        instance_curr_state = json.dumps(mstep_exectree.Get_node_states(instance_infra_id))
                        print()
                        logger.info('New consistent global state reached! Instance current state: {}'.format(instance_curr_state))

                        instance_index_next += 1

                        if (instance_index_next == len(path_states)):
                            break
                        else:
                            instance_next_desired_state = path_states[instance_index_next]
                            
                        print('*** Next desired state: {}'.format(instance_next_desired_state))

                        # Calculate nodes to step
                        current_state_dict = json.loads(instance_curr_state)
                        next_state_dict = json.loads(instance_next_desired_state)
                        node_names_to_step = []

                        for k, v in next_state_dict.items():
                            if (v != current_state_dict[k]):
                                node_names_to_step.append(k)
                            
                        print('*** Nodes to step: {}'.format(node_names_to_step))

                        # Get node IDs from node names for current infrastructure instance
                        node_ids = []
                        for act_node in node_names_to_step:
                            node_ids.append(mstep_repo.Read_node_id_from_node_name(instance_infra_id, act_node))
                            
                        print('*** Correspondig node IDs: {}'.format(node_ids))

                        # Step needed nodes, wait until next consistent state
                        Step_given_nodes(instance_infra_id, node_ids)
                        print()
                        mstep_logger.Print_infra(instance_infra_id)
                    else:
                        # Inconsistent global state, wait a bit
                        time.sleep(3)
                logger.info('Finished! Instance current state: {}'.format(instance_curr_state))
            else:
                logger.error('Orchestrator error!')

# Helper functions and methods
def Infra_exists(infra_id):
    """Decides if the given infrastructure already exists.

    Args:
        infra_id (string): An infrastructure ID.

    Returns:
        boolean: True if the infrastructure exists, False if not.
    """

    infras = mstep_repo.Read_infrastructure(infra_id)

    if len(infras) == 0:
        return False
    else:
        return True

def Node_exists(infra_id, node_id):
    """Checks if the given node within the given infrastructure exists or not.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.

    Returns:
        bool: True if the node exists in the given infrastructure, False if not.
    """

    nodes = mstep_repo.Read_node(infra_id, node_id)

    if len(nodes) == 0:
        return False
    else:
        return True

def Is_node_permission_true(infra_id, node_id):
    """Decides if the given node in the given infrastructure is permitted to move to the next breakpoint.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.

    Returns:
        bool: True if the node is permited, False if not.
    """

    node = mstep_repo.Read_node(infra_id, node_id)

    if (node[0][5] == 1):
        return True
    else:
        return False