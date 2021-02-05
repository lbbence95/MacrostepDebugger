# Represents logging functions

from data import repository as mstep_repo
from datetime import datetime
import logging

#Logger setup
logger = logging.getLogger('logger')
logger.propagate = False
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
formatter = logging.Formatter('*** (%(asctime)s): %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def List_all_infras():
    """Prints a list of managed infrastructures.
    """
    logger.info('Listing managed infrastructures:')

    infras = mstep_repo.Read_all_infrastructures()
    if len(infras) == 0:
        logger.info('No managed infrastructures!')
    else:
        logger.info('Managed infrastructures:')
        for act_infra in infras:
            print('*** "{}" ({}) registered at {}'.format(act_infra[0], act_infra[1], act_infra[2]))


def List_all_nodes():
    """Prints a list of managed nodes.
    """
    
    logger.info('Listing managed nodes:')

    nodes = mstep_repo.Read_all_nodes()
    if len(nodes) == 0:
        logger.info('No managed nodes!')
    else:
        logger.info('Managed nodes:')
        for act_node in nodes:
            last_bp = mstep_repo.Read_breakpoint(act_node[0], act_node[1])[-1]
            print('*** "{}" ("{}" in infrastructure "{}") at breakpoint {} (tags: {})'.format(act_node[1], act_node[2], act_node[0], act_node[4], last_bp[5]))

def List_all_infra_app_pairs():
    """Prints a list of currently tracked infrastructure-application pairs.
    """
    infra_app_pairs = mstep_repo.Read_all_trace_entry()

    if (len(infra_app_pairs) == 0):
        logger.info('No infrastructure-application pair is currently traced!')
    else:
        logger.info('Traced infrastructures:')
        for act_infra_app in infra_app_pairs:
            print('*** "{}" in application: "{}".'.format(act_infra_app[1], act_infra_app[0]))

def Print_infra(infra_id):
    """Prints the details of a single infrastructure.

    Args:
        infra_id (string): An infrastructure ID.
    """

    infra = mstep_repo.Read_infrastructure(infra_id)

    if len(infra) == 0:
        print('*** No infrastructure exists with ID "{}"!'.format(infra_id))
    else:
        for act_infra in infra:
            print('*** Details for infrastructure "{}" ({}) registered at {}.'.format(act_infra[0], act_infra[1], act_infra[2]))
        
        nodes = mstep_repo.Read_nodes_from_infra(infra_id)

        print('*** Nodes in infrastructure:')
        for act_node in nodes:
            last_bp = mstep_repo.Read_breakpoint(infra_id, act_node[1])[-1]
            print('*** "{}" ("{}") at breakpoint {} (tags: {}), can move to next breakpoint: {}'.format(act_node[1], act_node[2], act_node[4], last_bp[5], 'Yes' if act_node[5] == 1 else 'No'))

def Print_node(infra_id, node_id):
    """Prints the details of a single node.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.
    """

    node = mstep_repo.Read_node(infra_id, node_id)

    if len(node) == 0:
        print('*** No node with ID "{}" exists in infrastructure with ID "{}"!'.format(node_id, infra_id))
    else:
        for act_node in node:
            print('*** Node "{}" ("{}") is in infrastructure "{}"'.format(act_node[1], act_node[2], act_node[0]))
            print('*** Node public IP: {}'.format(act_node[6]))
            print('*** Can move to next breakpoint: {}'.format('Yes' if act_node[5] == 1 else 'No'))

        bps = mstep_repo.Read_breakpoint(infra_id, node_id)

        print('*** Node breakpoints:')

        for act_bp in bps:
            print('*** Reached breakpoint {} at {} (tags: {})'.format(act_bp[3], act_bp[2], act_bp[5]))

def Print_breakpoint_info(request_data):
    """Prints the received VM data to the console.

    Args:
        request_data (request): A request containing a JSON string.
    """

    json_data = request_data.get_json()

    # Infrastructure related data
    infra_id = json_data['infraData']['infraID']
    infra_name = json_data['infraData']['infraName']

    # Local breakpoint related data
    bp_tag = json_data['bpData']['bpTag']

    # Node related data
    node_publicIP = request_data.remote_addr
    node_id = json_data['nodeData']['nodeID']
    node_name = json_data['nodeData']['nodeName']
    node_data = json_data['nodeData']

    # Printing received information
    print('*** Infrastructure ID: {}'.format(infra_id))
    print('*** Infrastructure Name: {}'.format(infra_name))

    print('*** Node ID: {}'.format(node_id))
    print('*** Node Name: {}'.format(node_name))

    print('*** Breakpoint Tags: {}'.format(bp_tag))

    print('*** Node Data:')

    for dataKey in node_data:
        print('*** {}: {}'.format(dataKey, node_data[dataKey]))

    print('*** Node Public IP: {}\r\n'.format(node_publicIP))