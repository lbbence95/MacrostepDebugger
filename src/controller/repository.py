# Represent often used queries


import src.data.db as mstepdb


def InitializeDB():
    """Creates a new database.
    """
    mstepdb.InitializeDB()


### INFRASTRUCTURES
# CREATE
def RegisterInfrastructure(infraID, infra_name, register_timestamp):
    sql = '''INSERT INTO Infras (infraID, infraName, registered) VALUES (?,?,?)'''
    mstepdb.RegisterInfrastucture(sql, infraID, infra_name, register_timestamp)


# READ ALL
def GetAllInfrasturctures():
    sql = '''SELECT * FROM Infras'''
    return mstepdb.ReadInfrastructures(sql)


# READ SINGLE
def GetInfrastructure(infraID):
    """Returns the details of a given infrastrucutre.

    Args:
        infraID (string): An infrastructure ID.

    Returns:
        tuple: The details of the given infrastructure. If no such infrastructure exists, the returned tuple is empty.
    """
    sql = '''SELECT * FROM Infras WHERE infraID=(?) '''
    return mstepdb.ReadInfrastructure(sql, infraID)


# DELETE
def RemoveInfrastructure(infraID):
    pass


#### NODES
# CREATE
def RegisterNode(infraID, nodeID, nodeName, node_reg_timestamp, bpid):
    sql = '''INSERT INTO Nodes (infraID, nodeID, nodeName, nodeRegistered, currBP) VALUES (?,?,?,?,?)'''
    mstepdb.RegisterNode(sql, infraID, nodeID, nodeName, node_reg_timestamp, bpid)


# READ ALL
def GetAllNodes():
    sql = '''SELECT * FROM Nodes'''
    return mstepdb.ReadNodes(sql)


# READ SINGLE
def GetNode(infraID, nodeID):
    sql = '''SELECT * FROM Nodes WHERE infraID=(?) AND nodeID=(?)'''
    return mstepdb.ReadNode(sql, infraID, nodeID)

def ReadNodeBreakpoint(infraID, nodeID):
    sql = '''SELECT bpNum FROM Nodes WHERE infraID=(?) AND nodeID=(?)'''
    return mstepdb.ReadNode(sql, infraID, nodeID)


# UPDATE
def UpdateNodeBreakpoint(infraID, nodeID):
    sql = '''UPDATE Nodes SET currBP = currBP + 1, moveNext = 0 WHERE infraID=(?) AND nodeID=(?)'''
    return mstepdb.UpdateNode(sql, infraID, nodeID)


# BREAKPOINTS
# CREATE
def RegisterBreakpoint(infraID, nodeID, reg_timestamp, bpNum, nodeData):
    sql = '''INSERT INTO Breakpoints (infraID, nodeID, bpRegistered, bpNum, nodeData) VALUES (?,?,?,?,?)'''
    mstepdb.RegisterBreakpoint(sql, infraID, nodeID, reg_timestamp, bpNum, nodeData)

# READ ALL
def ReadBreakpoints():
    sql = '''SELECT * FROM Breakpoints'''
    return mstepdb.ReadBreakpoints(sql)