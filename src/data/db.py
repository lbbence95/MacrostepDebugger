# Represents the database layer of the application


import sqlite3


def InitializeDB():
    "Creates a new database if none exist, otherwise removes all previous data."

    db_conn = sqlite3.connect('src/data/mstepDB.db')
    curr = db_conn.cursor()

    # If the database file exists then drop all tables,
    # if not then create and initialize the database.

    # Infrastructures
    curr.execute("""DROP TABLE IF EXISTS Infras""")
    curr.execute("""CREATE TABLE Infras (
        infraID TEXT NOT NULL PRIMARY KEY,
        infraName TEXT,
        registered TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) """)

    # Nodes
    curr.execute("""DROP TABLE IF EXISTS Nodes""")
    curr.execute("""CREATE TABLE Nodes (
        infraID TEXT NOT NULL,
        nodeID TEXT NOT NULL,
        nodeName TEXT,
        nodeRegistered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        currBP INTEGER DEFAULT 0,
        moveNext INTEGER DEFAULT 0,
        PRIMARY KEY (infraID, nodeID, nodeRegistered)
    ) """)

    # Breakpoints
    curr.execute("""DROP TABLE IF EXISTS Breakpoints""")
    curr.execute("""CREATE TABLE Breakpoints (
        infraID TEXT NOT NULL,
        nodeID TEXT NOT NULL,
        bpRegistered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        bpNum INTEGER,
        nodeData TEXT,
        PRIMARY KEY (infraID, nodeID, bpNum)
    )""")

    db_conn.commit()
    db_conn.close()


# Infrastructures
# Create an infrastructure
def RegisterInfrastucture(sql, infraID, infra_name, register_timestamp):
    """Creates a new infrastructrure entry.

    Args:
        sql (string): Represents an SQL expression.
        infraID (string): An infrastructure ID.
        infra_name (string): The infrastructures name.
        register_timestamp (datetime): A timestamp stating the date and time of the registration.
    """

    infra_data = (infraID, infra_name, register_timestamp)

    db_conn = sqlite3.connect('src/data/mstepDB.db', detect_types=sqlite3.PARSE_DECLTYPES)

    curr = db_conn.cursor()
    curr.execute(sql, infra_data)
    
    db_conn.commit()
    db_conn.close()


# Read all infrastructures
def ReadInfrastructures(sql):
    """Reads the details of all infrastructures.

    Args:
        sql (string): Represents an SQL expression.

    Returns:
        tuple: The details of the infrastructures.
    """

    db_conn = sqlite3.connect('src/data/mstepDB.db')

    cur = db_conn.cursor()
    cur.execute(sql)

    result = cur.fetchall()

    db_conn.commit()
    db_conn.close()

    return result


# Read a single infrastructure
def ReadInfrastructure(sql, infraID):
    """Reads the details of a given infrastructure.

    Args:
        sql (string): Represents an SQL expression.
        infraID (string): An infrastructure ID.

    Returns:
        tuple: The details of the given infrastructure.
    """

    db_conn = sqlite3.connect('src/data/mstepDB.db')

    cur = db_conn.cursor()
    cur.execute(sql,(infraID,))

    result = cur.fetchall()

    db_conn.commit()
    db_conn.close()

    return result


# Delete an infrastrucuture
def DeleteInfrastucture(infra_name):
    pass


# Nodes
# Create a node
def RegisterNode(sql, infraID, nodeID, nodeName, node_reg_timestamp, bpid):

    node_tuple = (infraID, nodeID, nodeName, node_reg_timestamp, bpid)

    db_conn = sqlite3.connect('src/data/mstepDB.db', detect_types=sqlite3.PARSE_DECLTYPES)
    
    curr = db_conn.cursor()
    curr.execute(sql, node_tuple)
    
    db_conn.commit()
    db_conn.close()


# Read all nodes
def ReadNodes(sql):
    db_conn = sqlite3.connect('src/data/mstepDB.db')

    cur = db_conn.cursor()
    cur.execute(sql)

    result = cur.fetchall()

    db_conn.commit()
    db_conn.close()

    return result


# Read single node
def ReadNode(sql, infraID, nodeID):
    db_conn = sqlite3.connect('src/data/mstepDB.db')

    cur = db_conn.cursor()
    cur.execute(sql,(infraID,nodeID,))

    result = cur.fetchall()

    db_conn.commit()
    db_conn.close()

    return result


# Update node
def UpdateNode(sql, infraID, nodeID):

    node_tuple = (infraID, nodeID)

    db_conn = sqlite3.connect('src/data/mstepDB.db')

    curr = db_conn.cursor()
    curr.execute(sql, node_tuple)

    db_conn.commit()
    db_conn.close()


# Breakpoints
# Create
def RegisterBreakpoint(sql, infraID, nodeID, reg_timestamp, bpNum, nodeData):

    bp_tuple = (infraID, nodeID, reg_timestamp, bpNum, nodeData)

    db_conn = sqlite3.connect('src/data/mstepDB.db', detect_types=sqlite3.PARSE_DECLTYPES)

    curr = db_conn.cursor()
    curr.execute(sql, bp_tuple)
    
    db_conn.commit()
    db_conn.close()


# Read all
def ReadBreakpoints(sql):

    db_conn = sqlite3.connect('src/data/mstepDB.db')

    cur = db_conn.cursor()
    cur.execute(sql)

    result = cur.fetchall()

    db_conn.commit()
    db_conn.close()

    return result


# Read single
def ReadBreakpoint(sql):
    pass