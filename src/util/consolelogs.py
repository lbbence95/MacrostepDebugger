# Contains functions for console logging.


from datetime import datetime
import src.controller.repository as msteprepo


def PrintConsoleInvalidData():
    """Prints an error message stating the received data were invalid.
    """

    print('*** MSTEP DEBUGGER\r\nReceived INVALID data at DEBUGGER localtime: {}'.format(datetime.now().strftime('%H:%M:%S.%f')[:-3]))
    print('*** End Of Report\r\n*** MSTEP DEBUGGER')


def PrintConsoleRequestData(request_data):
    """Prints the received VM data to the console.

    Args:
        request_data (string): The JSON string received from the VM endpoint.
    """

    json_data = request_data.get_json()

    # Infrastructure related data
    infraID = json_data['infraData']['infraID']
    infraName = json_data['infraData']['infraName']

    # Local breakpoint related data
    bpID = json_data['bpData']['bpNum']
    bpName = json_data['bpData']['bpName']

    # Node related data
    node_publicIP = request_data.remote_addr
    nodeID = json_data['nodeData']['nodeID']
    nodeName = json_data['nodeData']['nodeName']
    nodeData = json_data['nodeData']

    # Printing received information
     
    print('*** MSTEP DEBUGGER\r\nReceived VALID data at DEBUGGER localtime: {}'.format(datetime.now().strftime('%H:%M:%S.%f')[:-3]))

    print('\r\nFrom infrastructure with ID: {}'.format(infraID))
    print('From infrastructure with Name: {}\r\n'.format(infraName))

    print('From node with ID: {}'.format(nodeID))
    print('From node with Name: {}\r\n'.format(nodeName))

    print('Local breakpoint Number: {}'.format(bpID))
    print('Local breakpoint description: {}\r\n'.format(bpName))

    print('Node Data:')

    for dataKey in nodeData:
        print('{} is: {}'.format(dataKey, nodeData[dataKey]))

    print('nodePublicIP is: {}'.format(node_publicIP))

    print('\r\n*** End Of Report\r\n*** MSTEP DEBUGGER')


def PrintManagedInfras():
    """Prints the details of managed infrastructures to the console.
    """

    infras = msteprepo.GetAllInfrasturctures()

    if len(infras) == 0:
        print("*** No managed infrastuctures!")
    else:
        print("*** Managed infrastuctures:")

        for act_infra in infras:
            print('*** {}'.format(act_infra))


def PrintManagedNodes():
    """Prints the details of managed nodes to the console.
    """

    nodes = msteprepo.GetAllNodes()

    if len(nodes) == 0:
        print("*** No managed nodes!")
    else:
        print('*** Managed nodes:')

        for act_node in nodes:
            print('*** {}'.format(act_node))


def PrintBreakpoints():
    """Prints the details of stored breakpoints to the console.
    """

    bps = msteprepo.ReadBreakpoints()

    if len(bps) == 0:
        print("*** No breakpoints received yet!")
    else:
        print("*** Collected breakpoints:")

        for act_bp in bps:
            print('*** {}'.format(act_bp))