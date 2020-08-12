# Represent often used queries


import src.data.db as mstepdb


def InitializeDB():
    """Creates a new database.
    """
    mstepdb.InitializeDB()


### Create
# Create infrastructure
def RegisterInfrastructure(infra_id, infra_name, registered_timestamp):
    sql = '''INSERT INTO Infras (infraID, infraName, registered) VALUES (?,?,?)'''
    mstepdb.RegisterInfrastucture(sql, infra_id, infra_name, registered_timestamp)


# Create node
def RegisterNode(infra_id, node_id, node_name, registered_timestamp, bp_id):
    sql = '''INSERT INTO Nodes (infraID, nodeID, nodeName, nodeRegistered, currBP) VALUES (?,?,?,?,?)'''
    mstepdb.RegisterNode(sql, infra_id, node_id, node_name, registered_timestamp, bp_id)


# Create breakpoint
def RegisterBreakpoint(infra_id, node_id, registered_timestamp, bp_id, node_data):

    sql = '''INSERT INTO Breakpoints (infraID, nodeID, bpRegistered, bpNum, nodeData) VALUES (?,?,?,?,?)'''
    mstepdb.RegisterBreakpoint(sql, infra_id, node_id, registered_timestamp, bp_id, node_data)


### Read
# Read all infrastructures
def ReadAllInfrasturctures():
    sql = '''SELECT * FROM Infras'''
    return mstepdb.ReadInfrastructures(sql)


# Read single infrastructure
def ReadInfrastructure(infra_id):
    sql = '''SELECT * FROM Infras WHERE infraID=(?)'''

    infra_tuple = (infra_id,)

    return mstepdb.ReadInfrastructure(sql, infra_tuple)


# Read all node
def ReadAllNodes():
    sql = '''SELECT * FROM Nodes'''
    return mstepdb.ReadNodes(sql)


# Read single node
def ReadNode(infra_id, node_id):

    node_tuple = (infra_id, node_id)

    sql = '''SELECT * FROM Nodes WHERE infraID=(?) AND nodeID=(?)'''
    return mstepdb.ReadNode(sql, node_tuple)


# Read multiple node
def ReadNodesFromInfra(infraID):

    node_tuple = (infraID,)

    sql = '''SELECT * FROM Nodes WHERE infraID=(?)'''
    return mstepdb.ReadNode(sql, node_tuple)


# Read all breakpoints
def ReadBreakpoints():
    sql = '''SELECT * FROM Breakpoints'''
    return mstepdb.ReadBreakpoints(sql)


# Read breakpoint
def ReadBreakpoint(infraID, nodeID):
    sql = '''SELECT * FROM Breakpoints WHERE infraID=(?) AND nodeID=(?)'''

    bp_tuple = (infraID, nodeID)

    return mstepdb.ReadBreakpoint(sql, bp_tuple)


# Read breakpoint number
def ReadNodeBreakpoint(infraID, nodeID):

    node_tuple = (infraID, nodeID)

    sql = '''SELECT bpNum FROM Nodes WHERE infraID=(?) AND nodeID=(?)'''
    return mstepdb.ReadNode(sql, node_tuple)


# Update
# Update breakpoint and node permission
def UpdateNodeBreakpoint(infraID, nodeID):
    sql = '''UPDATE Nodes SET currBP = currBP + 1, moveNext = 0 WHERE infraID=(?) AND nodeID=(?)'''

    node_tuple = (infraID, nodeID)

    mstepdb.UpdateNode(sql, node_tuple)


# Update node permission
def UpdateSpecificNodeMoveNext(infraID, nodeID):
    sql = '''UPDATE Nodes SET moveNext = 1 WHERE infraID=(?) AND nodeID=(?)'''

    node_tuple = (infraID, nodeID)

    mstepdb.UpdateNode(sql, node_tuple)