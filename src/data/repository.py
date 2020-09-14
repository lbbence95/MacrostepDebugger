# Represent often used queries

import src.data.db as mstepdb

def InitializeDB():
    """Creates a new database.
    """
    mstepdb.InitializeDB()

### Create
# Create infrastructure
def RegisterInfrastructure(infra_id, infra_name, registered_timestamp):
    """Register an infrastructure.

    Args:
        infra_id (string): An infrastructure ID.
        infra_name (string): An infrastructure name.
        registered_timestamp (datetime): A timestamp indicating the time of the creation.
    """
    sql = '''INSERT INTO Infras (infraID, infraName, registered) VALUES (?,?,?)'''
    mstepdb.RegisterInfrastucture(sql, infra_id, infra_name, registered_timestamp)

# Create node
def RegisterNode(infra_id, node_id, node_name, registered_timestamp, bp_id, public_ip):
    """Register a node.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.
        node_name (string): A node name
        registered_timestamp (datetime): A timestamp indicating the time of the creation.
        bp_id (int): A breakpoint number.
        public_ip (string): An IP address.
    """
    sql = '''INSERT INTO Nodes (infraID, nodeID, nodeName, nodeRegistered, currBP, publicIP) VALUES (?,?,?,?,?,?)'''
    mstepdb.RegisterNode(sql, infra_id, node_id, node_name, registered_timestamp, bp_id, public_ip)

# Create breakpoint
def RegisterBreakpoint(infra_id, node_id, registered_timestamp, bp_id, node_data, bp_tag):
    """Register a breakpoint.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.
        registered_timestamp (datetime): A timestamp indicating the time of the creation.
        bp_id (int): A breakpoint number.
        node_data (string): A JSON string containing the details of the breakpoint.
        bp_tag (string): A list of tags in one string.
    """
    sql = '''INSERT INTO Breakpoints (infraID, nodeID, bpRegistered, bpNum, nodeData, bpTag) VALUES (?,?,?,?,?,?)'''
    mstepdb.RegisterBreakpoint(sql, infra_id, node_id, registered_timestamp, bp_id, node_data, bp_tag)

### Read
# Read all infrastructures
def ReadAllInfrasturctures():
    """Read all infrastructures.

    Returns:
        list: A list of infrastructures.
    """
    sql = '''SELECT * FROM Infras'''
    return mstepdb.ReadInfrastructures(sql)

# Read single infrastructure
def ReadInfrastructure(infra_id):
    """Reads a single infrastructure.

    Args:
        infra_id (string): An infrastructure ID.

    Returns:
        list: A list of infrastructures.
    """
    sql = '''SELECT * FROM Infras WHERE infraID=(?)'''
    infra_tuple = (infra_id,)
    return mstepdb.ReadInfrastructure(sql, infra_tuple)

# Read all node
def ReadAllNodes():
    """Read all nodes.

    Returns:
        list: A list of nodes.
    """
    sql = '''SELECT * FROM Nodes'''
    return mstepdb.ReadNodes(sql)

# Read single node
def ReadNode(infra_id, node_id):
    """Read the details of a single node.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.

    Returns:
        list: A list of nodes.
    """
    node_tuple = (infra_id, node_id)
    sql = '''SELECT * FROM Nodes WHERE infraID=(?) AND nodeID=(?)'''
    return mstepdb.ReadNode(sql, node_tuple)

# Read multiple node
def ReadNodesFromInfra(infra_id):
    """Read nodes from a given infrastructure.

    Args:
        infra_id (string): An infrastructure ID.

    Returns:
        list: A list of nodes.
    """
    node_tuple = (infra_id,)
    sql = '''SELECT * FROM Nodes WHERE infraID=(?)'''
    return mstepdb.ReadNode(sql, node_tuple)

# Read all breakpoints
def ReadBreakpoints():
    """Read all stored breakpoint.

    Returns:
        list: A list of breakpoints.
    """
    sql = '''SELECT * FROM Breakpoints'''
    return mstepdb.ReadBreakpoints(sql)

# Read breakpoint
def ReadBreakpoint(infra_id, node_id):
    """Read the breakpoints of a single node.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.

    Returns:
        list: A list of the given node's breakpoints.
    """
    sql = '''SELECT * FROM Breakpoints WHERE infraID=(?) AND nodeID=(?)'''
    bp_tuple = (infra_id, node_id)
    return mstepdb.ReadBreakpoint(sql, bp_tuple)

# Read breakpoint number
def ReadNodeBreakpoint(infra_id, node_id):
    """Reads the breakpoint numbers of a given node.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.

    Returns:
        list: A list of breakpoint number of the given node.
    """
    node_tuple = (infra_id, node_id)
    sql = '''SELECT bpNum FROM Nodes WHERE infraID=(?) AND nodeID=(?)'''
    return mstepdb.ReadNode(sql, node_tuple)

# Update
# Update breakpoint and node permission
def UpdateNodeBreakpoint(infra_id, node_id):
    """Updates a given node's current breakpoint and it's permission to move to the next breakpoint.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.
    """
    sql = '''UPDATE Nodes SET currBP = currBP + 1, moveNext = 0 WHERE infraID=(?) AND nodeID=(?)'''
    node_tuple = (infra_id, node_id)
    mstepdb.UpdateNode(sql, node_tuple)

# Update node permission
def UpdateSpecificNodeMoveNext(infra_id, node_id):
    """Permit a given node to move to the next breakpoint.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.
    """
    sql = '''UPDATE Nodes SET moveNext = 1 WHERE infraID=(?) AND nodeID=(?)'''
    node_tuple = (infra_id, node_id)
    mstepdb.UpdateNode(sql, node_tuple)