# Contains functions for console logging.

from datetime import datetime
import src.controller.repository as msteprepo

def PrintConsoleInvalidData():
    """Prints an error message stating the received data were invalid.
    """

    print('*** MSTEP DEBUGGER\r\n*** Received INVALID data at DEBUGGER localtime: {}'.format(datetime.now().strftime('%H:%M:%S.%f')[:-3]))

def PrintConsoleRequestData(request_data):
    """Prints the received VM data to the console.

    Args:
        request_data (request): A request which contains the JSON string received from the VM endpoint.
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
    print('*** MSTEP DEBUGGER\r\n*** Received VALID data at DEBUGGER localtime: {}'.format(datetime.now().strftime('%H:%M:%S.%f')[:-3]))

    print('\r\n*** From infrastructure with ID: {}'.format(infra_id))
    print('*** From infrastructure with Name: {}\r\n'.format(infra_name))

    print('*** From node with ID: {}'.format(node_id))
    print('*** From node with Name: {}\r\n'.format(node_name))

    print('*** Local breakpoint Number: {}'.format(bp_id))
    print('*** Local breakpoint description: {}\r\n'.format(bp_tag))

    print('*** Node Data:')

    for dataKey in node_data:
        print('*** {}: {}'.format(dataKey, node_data[dataKey]))

    print('*** nodePublicIP: {}'.format(node_publicIP))
    print('\r\n*** MSTEP DEBUGGER')

def PrintManagedInfras():
    """Prints the details of managed infrastructures.
    """

    infras = msteprepo.ReadAllInfrasturctures()

    if len(infras) == 0:
        print("*** No managed infrastuctures!")
    else:
        print("*** Managed infrastuctures:")

        for act_infra in infras:
            print('*** {} ({}) registered at {}'.format(act_infra[0], act_infra[1], act_infra[2]))

def PrintManagedNodes():
    """Prints the details of managed nodes.
    """

    nodes = msteprepo.ReadAllNodes()

    if len(nodes) == 0:
        print("*** No managed nodes!")
    else:
        print('*** Managed nodes:')

        ### TO-DO: include breakpoint tags

        for act_node in nodes:
            print('*** {} ({} in infrastructure {}) at breakpoint {}.'.format(act_node[1], act_node[2], act_node[0], act_node[4]))

def PrintBreakpoints():
    """Prints the details of stored breakpoints to the console.
    """

    bps = msteprepo.ReadBreakpoints()

    if len(bps) == 0:
        print("*** No breakpoints received yet!")
    else:
        print("*** Collected breakpoints:")

        ### TO-DO: Print breakpoints in a mannered format

        for act_bp in bps:
            print('*** {}'.format(act_bp))

def PrintInfra(infra_id):
    """Print the details of a single infrastructure.

    Args:
        infra_id (string): An infrastructure ID.
    """

    infras = msteprepo.ReadInfrastructure(infra_id)

    if len(infras) == 0:
        print('*** No infrastructure exists with ID {}!'.format(infra_id))
    else:

        for act_infra in infras:
            print('\r\n*** Details for infrastructure {} ({}) registered at {}'.format(act_infra[0], act_infra[1], act_infra[2]))
        
        nodes = msteprepo.ReadNodesFromInfra(infra_id)

        print('*** Nodes in infrastructure:')

        ### TO-DO: print last breakpoint tags (repo 'getLastBreakpoint' call)

        for act_node in nodes:
            print('*** {} ({}) at breakpoint {}.'.format(act_node[1], act_node[2], act_node[4]))

def PrintNode(infra_id, node_id):
    
    nodes = msteprepo.ReadNode(infra_id, node_id)

    if len(nodes) == 0:
        print('*** No node with ID {} exists in infrastructure with ID {}!'.format(node_id, infra_id))
    else:
        for act_node in nodes:
            print('\r\n*** Details for node {} ({}) in infrastructure {}:'.format(act_node[1], act_node[2], act_node[0]))
            print('*** Node public IP: {}'.format(act_node[6]))
            ### TO-DO: 1 - Yes, 0 - No conversion
            print('*** Can move to next breakpoint: {}'.format(act_node[5]))

        bps = msteprepo.ReadBreakpoint(infra_id, node_id)

        print('*** Node breakpoints:')

        ### TO-DO: Breakpoint history (tags)

        for act_bp in bps:
            print('*** Reached breakpoint {} at {} (tags: {})'.format(act_bp[3], act_bp[2], act_bp[5]))

### TO-DO: Generic error printer
def ErrorPrinter(message):
    pass