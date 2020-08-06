# Represents the controller module of the macrostep based debugger

import src.controller.repository as msteprepo

def InitializeDB():
    """Initializes a new database.
    """
    msteprepo.InitializeDB()


def InfraExists(infraID):
    """Decides if the given infrastructure is already registered.

    Args:
        infraID (string): The searched infrastructure ID.

    Returns:
        boolean: True if the infrastructure exists, False if not.
    """

    infras = msteprepo.GetInfrastructure(infraID)

    if len(infras) == 0:
        return False
    else:
        return True


def IsNewBreakpointNext(infraID, nodeID, bpid):

    try:
        stored_bp = (msteprepo.GetNode(infraID, nodeID))[0][4]
        if (int(stored_bp) + 1) == bpid:
            return True
        else:
            return False
    except IndexError:
        return False


def NodeExists(infraID, nodeID):
    """Checks if the given node within the given infrastrucutre exists or not.

    Args:
        infraID (string): An infrastructure ID.
        nodeID (string): A node ID.

    Returns:
        boolean: True if the node exists in the given infrastructure, False if not.
    """

    nodes = msteprepo.GetNode(infraID, nodeID)

    if len(nodes) == 0:
        return False
    else:
        return True


def RegisterInfrastructure(infraID, infra_name, registrationDate):

    if infraID != None and infraID != "" and registrationDate != None:
        msteprepo.RegisterInfrastructure(infraID, infra_name, registrationDate)
    else:
        # TO-DO: Throw some error
        pass


def RegisterNode(infraID, nodeID, nodeName, node_reg_timestamp, bpid):
    if (infraID != None and infraID != "") and (nodeID != None and nodeID != "") and node_reg_timestamp != None:
        msteprepo.RegisterNode(infraID, nodeID, nodeName, node_reg_timestamp, bpid)
    else:
        # TO-DO: Throw some error
        pass


def UpdateNodeBreakpoint(ifnraId, nodeID):
    if (ifnraId != None and ifnraId != "") and (nodeID != None and nodeID != ""):
        msteprepo.UpdateNodeBreakpoint(ifnraId, nodeID)
    else:
        # TO-DO: Throw some error
        pass


def RegisterBreakpoint(infraID, nodeID, reg_timestamp, bpNum, nodeData):
    if (infraID != None and infraID != "") and (nodeID != None and nodeID != "") and bpNum > 0:
        msteprepo.RegisterBreakpoint(infraID, nodeID, reg_timestamp, bpNum, nodeData)
    else:
        # TO-DO: Throw some error
        pass