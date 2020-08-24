# Represents the controller module of the macrostep based debugger

import src.controller.repository as msteprepo
import datetime, json

def Initialize():
    """Initializes a new database.
    """
    msteprepo.InitializeDB()

def CanNodeMoveNext(infra_id, node_id):
    """Decides if the given node in the given infrastructure is permitted to move to the next breakpoint.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.

    Returns:
        bool: True if the node is permited, False if not.
    """

    node = msteprepo.ReadNode(infra_id, node_id)

    if node[0][5] == 1:
        return True
    else:
        return False

def InfraExists(infra_id):
    """Decides if the given infrastructure is already registered.

    Args:
        infra_id (string): The searched infrastructure ID.

    Returns:
        boolean: True if the infrastructure exists, False if not.
    """

    infras = msteprepo.ReadInfrastructure(infra_id)

    if len(infras) == 0:
        return False
    else:
        return True

def IsNewBreakpointNext(infra_id, node_id, bp_id):
    """Determines if the received breakpoint is the next breakpoint.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.
        bp_id (int): A breakpoint number.

    Returns:
        bool: True or false.
    """

    try:
        stored_bp = (msteprepo.ReadNode(infra_id, node_id))[0][4]
        if (int(stored_bp) + 1) == bp_id:
            return True
        else:
            return False
    except IndexError:
        return False

def NodeExists(infra_id, node_id):
    """Checks if the given node within the given infrastrucutre exists or not.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.

    Returns:
        boolean: True if the node exists in the given infrastructure, False if not.
    """

    nodes = msteprepo.ReadNode(infra_id, node_id)

    if len(nodes) == 0:
        return False
    else:
        return True

def ProcessJSON(public_ip, json_data):
    # return is a tupple: code, message, success

    infra_name = json_data['infraData']['infraName']
    infra_id = json_data['infraData']['infraID']
    node_name = json_data['nodeData']['nodeName']
    node_id = json_data['nodeData']['nodeID']
    bp_tag = json_data['bpData']['bpTag']
    bp_id = int(json.dumps(json_data['bpData']['bpNum']))

    if InfraExists(infra_id) == False:
        # Check if the breakpoint ID is 1. Otherwise return invalid request.
        if (bp_id == 1) == True:
            # Valid breakpoint ID. Register the infrastructure, the node, and the breakpoint.
            msteprepo.RegisterInfrastructure(infra_id, infra_name, datetime.datetime.now().strftime('%Y.%m.%d. %H:%M:%S.%f')[:-3])
            msteprepo.RegisterNode(infra_id, node_id, node_name, datetime.datetime.now().strftime('%Y.%m.%d. %H:%M:%S.%f')[:-3], bp_id, public_ip)
            msteprepo.RegisterBreakpoint(infra_id, node_id, datetime.datetime.now().strftime('%Y.%m.%d. %H:%M:%S.%f')[:-3], bp_id, str(json_data), bp_tag)

            print("*** New infrastructure added!")
            print("*** New node added!")
            print("*** New breakpoint added!")

            return (200, 'Valid JSON. New infrastructure, node and breakpoint added.', True)
        else:
            return (422, 'Invalid breakpoint ID.', False)
    else:
        if NodeExists(infra_id, node_id) == False:
            # Check if the breakpoint ID is 1. Otherwise return invalid request.
            if (bp_id == 1) == True:
                # Valid breakpoint ID. The infrastructure exists, but the new node does not. Register the node and the new BP.
                msteprepo.RegisterNode(infra_id, node_id, node_name, datetime.datetime.now().strftime('%Y.%m.%d. %H:%M:%S.%f')[:-3], bp_id, public_ip)
                msteprepo.RegisterBreakpoint(infra_id, node_id, datetime.datetime.now().strftime('%Y.%m.%d. %H:%M:%S.%f')[:-3], bp_id, str(json_data), bp_tag)

                print("*** New node added!")
                print("*** New breakpoint added!")

                return (200, 'Valid JSON. New node and breakpoint added.', True)
            else:
                return (422, 'Invalid breakpoint ID.', False)  
        else:
            # The infrastructure and the node exists. Check if this is a valid new breakpoint.
            if IsNewBreakpointNext(infra_id, node_id, bp_id) == True:          
                # Valid new breakpoint. Register the new BP, and update the node to the retreived BP ID.
                UpdateNodeBreakpoint(infra_id, node_id)
                msteprepo.RegisterBreakpoint(infra_id, node_id, datetime.datetime.now().strftime('%Y.%m.%d. %H:%M:%S.%f')[:-3], bp_id, str(json_data), bp_tag)

                print("*** Node updated!")
                print("*** New breakpoint added!")

                return (200, 'Valid JSON. New breakpoint added, node status updated.', True)
            else:
                # The infrastructure and the node exists, but this is not a valid breakpoint.
                return (422, 'Invalid breakpoint ID.', False)

def UpdateNodeBreakpoint(infra_id, node_id):
    """Updates a given node (update). This method updates the breakpoint to the next breakpoint, and updates the permission of moving to the next breakpoint to False (0).

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.
    """

    if (infra_id != None and infra_id != "") and (node_id != None and node_id != ""):
        msteprepo.UpdateNodeBreakpoint(infra_id, node_id)
    else:
        # TO-DO: Throw some error
        pass

def MoveNodeToNext(infra_id, node_id):
    """Updates the given nodes permission of moving to the next breakpoint to True.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.
    """
    msteprepo.UpdateSpecificNodeMoveNext(infra_id, node_id)