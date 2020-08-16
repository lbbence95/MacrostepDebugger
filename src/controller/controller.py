# Represents the controller module of the macrostep based debugger

import src.controller.repository as msteprepo

def InitializeDB():
    """Initializes a new database.
    """
    msteprepo.InitializeDB()

def CanNodeMoveNext(infra_id, node_id):
    """Decides if the given node in the given infrastructure is permited to move to the next breakpoint.

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

def RegisterInfrastructure(infra_id, infra_name, registration_date):
    """Registers a new infrastructure (create).

    Args:
        infra_id (string): An infrastructure ID.
        infra_name (string): The name of the ifnrastructure.
        registration_date (datetime): The date and time when the infrastructure is registered.
    """

    if infra_id != None and infra_id != "" and registration_date != None:
        msteprepo.RegisterInfrastructure(infra_id, infra_name, registration_date)
    else:
        # TO-DO: Throw some error
        pass

def RegisterNode(infra_id, node_id, node_name, registration_timestamp, bp_id, public_ip):
    """Registers a new node (create).

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.
        node_name (string): The name of the node.
        registration_timestamp (datetime): The date and time when the node is registered.
        bp_id (int): The number of the received breakpoint.
    """

    if (infra_id != None and infra_id != "") and (node_id != None and node_id != "") and registration_timestamp != None:
        msteprepo.RegisterNode(infra_id, node_id, node_name, registration_timestamp, bp_id, public_ip)
    else:
        # TO-DO: Throw some error
        pass

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

def RegisterBreakpoint(infra_id, node_id, registration_timestamp, bp_num, node_data, bp_tag):
    """Registers a new breakpoint (create).

    Args:
        infra_id (string): An ifnrastructure ID.
        node_id (string): A node ID.
        registration_timestamp (datetime): A timestamp of when the breakpoint was registered.
        bp_num (int): The breakpoint's unique number.
        node_data (string): A JSON string.
        bp_tag (string): A description of the breakpoint (e.g.: tags).
    """

    if (infra_id != None and infra_id != "") and (node_id != None and node_id != "") and bp_num > 0:
        msteprepo.RegisterBreakpoint(infra_id, node_id, registration_timestamp, bp_num, node_data, bp_tag)
    else:
        # TO-DO: Throw some error
        pass