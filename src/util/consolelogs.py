# Contains functions for console logging.

import datetime
import src.controller.repository as msteprepo

def PrintConsoleInvalidData():
    """Prints a message stating the received data were invalid.
    """
    print('\r\n*** ({}) Received INVALID breakpoint data.'.format(datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]))

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
    print('\r\n*** ({}) Received VALID breakpoint data.'.format(datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]))

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

def PrintManagedInfras():
    """Prints the details of managed infrastructures.
    """

    infras = msteprepo.ReadAllInfrasturctures()

    if len(infras) == 0:
        print('\r\n*** ({}) No managed infrastuctures!'.format(datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]))
    else:
        print('\r\n*** ({}) Managed infrastuctures:'.format(datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]))

        for act_infra in infras:
            print('*** "{}" ({}) registered at {}'.format(act_infra[0], act_infra[1], act_infra[2]))

def PrintManagedNodes():
    """Prints the details of managed nodes.
    """

    nodes = msteprepo.ReadAllNodes()

    if len(nodes) == 0:
        print('\r\n*** ({}) No managed nodes!'.format(datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]))
    else:
        print('\r\n*** ({}) Managed nodes:'.format(datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]))

        for act_node in nodes:
            last_bp = msteprepo.ReadBreakpoint(act_node[0], act_node[1])[-1]
            print('*** "{}" ("{}" in infrastructure "{}") at breakpoint {} (tags: {})'.format(act_node[1], act_node[2], act_node[0], act_node[4], last_bp[5]))

def PrintBreakpoints():
    """Prints the details of stored breakpoints.
    """

    bps = msteprepo.ReadBreakpoints()

    if len(bps) == 0:
        print('\r\n*** ({}) No breakpoints received yet!'.format(datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]))
    else:
        print('\r\n*** ({}) Collected breakpoints:'.format(datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]))

        for act_bp in bps:
            print('*** {}'.format(act_bp))

def PrintInfra(infra_id):
    """Prints the details of a single infrastructure.

    Args:
        infra_id (string): An infrastructure ID.
    """

    infras = msteprepo.ReadInfrastructure(infra_id)

    if len(infras) == 0:
        print('\r\n*** ({}) No infrastructure exists with ID "{}"!'.format(datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3], infra_id))
    else:

        for act_infra in infras:
            print('\r\n*** ({}) Details for infrastructure "{}" ({}) registered at {}.'.format(datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3], act_infra[0], act_infra[1], act_infra[2]))
        
        nodes = msteprepo.ReadNodesFromInfra(infra_id)

        print('*** Nodes in infrastructure:')

        for act_node in nodes:
            last_bp = msteprepo.ReadBreakpoint(infra_id, act_node[1])[-1]
            print('*** "{}" ("{}") at breakpoint {} (tags: {})'.format(act_node[1], act_node[2], act_node[4], last_bp[5]))

def PrintNode(infra_id, node_id):
    """Prints the details of a single node.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.
    """
    
    nodes = msteprepo.ReadNode(infra_id, node_id)

    if len(nodes) == 0:
        print('*** ({}) No node with ID "{}" exists in infrastructure with ID "{}"!'.format(datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3], node_id, infra_id))
    else:
        for act_node in nodes:
            print('\r\n*** ({}) Details for node "{}" ("{}") in infrastructure "{}":'.format(datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3], act_node[1], act_node[2], act_node[0]))
            print('*** Node public IP: {}'.format(act_node[6]))
            print('*** Can move to next breakpoint: {}'.format('Yes' if act_node[5] == 1 else 'No'))

        bps = msteprepo.ReadBreakpoint(infra_id, node_id)

        print('*** Node breakpoints:')

        for act_bp in bps:
            print('*** Reached breakpoint {} at {} (tags: {})'.format(act_bp[3], act_bp[2], act_bp[5]))