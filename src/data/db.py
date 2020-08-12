# Represents the database layer of the application


import sqlite3

# TO-DO: Store actual datetime not jsut time

def InitializeDB():
    "Creates a new database if none exists, otherwise removes all previous data."

    db_conn = sqlite3.connect('src/data/mstepDB.db')
    curr = db_conn.cursor()

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


### Create
# Create infrastructure
def RegisterInfrastucture(sql, infra_id, infra_name, registered_timestamp):
    """Creates a new infrastructrure entry.

    Args:
        sql (string): Represents an SQL expression.
        infra_id (string): An infrastructure ID.
        infra_name (string): The infrastructures name.
        registered_timestamp (datetime): A timestamp stating the date and time of the registration.
    """

    infra_tuple = (infra_id, infra_name, registered_timestamp)

    db_conn = sqlite3.connect('src/data/mstepDB.db', detect_types=sqlite3.PARSE_DECLTYPES)

    curr = db_conn.cursor()
    curr.execute(sql, infra_tuple)
    
    db_conn.commit()
    db_conn.close()


# Create node
def RegisterNode(sql, infra_id, node_id, node_name, registered_timestamp, bp_id):
    """Creates a new node entry.

    Args:
        sql (string): Represents an SQL expression.
        infra_id (string): An infrastructure ID.
        node_id (string): A node id.
        node_name (string): The name of the node.
        registered_timestamp (datetime): A timestamp stating the date and time of the registration.
        bp_id (int): The current breakpoint.
    """

    node_tuple = (infra_id, node_id, node_name, registered_timestamp, bp_id)

    db_conn = sqlite3.connect('src/data/mstepDB.db', detect_types=sqlite3.PARSE_DECLTYPES)
    
    curr = db_conn.cursor()
    curr.execute(sql, node_tuple)
    
    db_conn.commit()
    db_conn.close()


# Create breakpoint
def RegisterBreakpoint(sql, infra_id, node_id, registered_timestamp, bp_id, node_data):
    """Creates a new breakpoint entry.

    Args:
        sql (string): Represents an SQL expression.
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.
        registered_timestamp (datetime): A timestamp stating the date and time of the registration.
        bp_id (int): The current breakpoint.
        node_data ([type]): A JSON string containing containing data about the breakpoint.
    """

    bp_tuple = (infra_id, node_id, registered_timestamp, bp_id, node_data)

    db_conn = sqlite3.connect('src/data/mstepDB.db', detect_types=sqlite3.PARSE_DECLTYPES)

    curr = db_conn.cursor()
    curr.execute(sql, bp_tuple)
    
    db_conn.commit()
    db_conn.close()


### Read
# Read all infrastructures
def ReadInfrastructures(sql):
    """Reads the details of all infrastructures.

    Args:
        sql (string): Represents an SQL expression.

    Returns:
        list: The details of the infrastructures in a list.
    """

    db_conn = sqlite3.connect('src/data/mstepDB.db')

    cur = db_conn.cursor()
    cur.execute(sql)

    result = cur.fetchall()

    db_conn.commit()
    db_conn.close()

    return result


# Read a single infrastructure
def ReadInfrastructure(sql, infra_tuple):
    """Reads the details of a given infrastructure.

    Args:
        sql (string): Represents an SQL expression.
        infraID (string): An infrastructure ID.

    Returns:
        tuple: The details of the given infrastructure.
    """

    db_conn = sqlite3.connect('src/data/mstepDB.db')

    cur = db_conn.cursor()
    cur.execute(sql, infra_tuple)

    result = cur.fetchall()

    db_conn.commit()
    db_conn.close()

    return result


# Read all nodes
def ReadNodes(sql):
    """Reads the details of managed nodes.

    Args:
        sql (string): An SQL expression.

    Returns:
        list: List of nodes.
    """

    db_conn = sqlite3.connect('src/data/mstepDB.db')

    cur = db_conn.cursor()
    cur.execute(sql)

    result = cur.fetchall()

    db_conn.commit()
    db_conn.close()

    return result


# Read single node
def ReadNode(sql, node_tuple):
    """Reads node(s) according to the supplied SQL statement.

    Args:
        sql (string): An SQL expression.
        node_tuple (tuple): A set of data to be substituted into the SQL statement.

    Returns:
        list: A list of nodes.
    """

    db_conn = sqlite3.connect('src/data/mstepDB.db')

    cur = db_conn.cursor()
    cur.execute(sql, node_tuple)

    result = cur.fetchall()

    db_conn.commit()
    db_conn.close()

    return result


# Read all breakpoints
def ReadBreakpoints(sql):
    """Reads all breakpoints from the database.

    Args:
        sql (string): An SQL statement.

    Returns:
        list: A list of breakpoints.
    """

    db_conn = sqlite3.connect('src/data/mstepDB.db')

    cur = db_conn.cursor()
    cur.execute(sql)

    result = cur.fetchall()

    db_conn.commit()
    db_conn.close()

    return result


# Read single
def ReadBreakpoint(sql, bp_tuple):
    """Reads breakpoint(s) according to the given SQL statement.

    Args:
        sql (string): An SQL expression.
        bp_tuple (tuple): A set of data to be substituted into the SQL statement.

    Returns:
        list: A list of breakpoints.
    """

    db_conn = sqlite3.connect('src/data/mstepDB.db')

    cur = db_conn.cursor()
    cur.execute(sql, bp_tuple)

    result = cur.fetchall()

    db_conn.commit()
    db_conn.close()

    return result


# Update
# Update node
def UpdateNode(sql, node_tuple):

    db_conn = sqlite3.connect('src/data/mstepDB.db')

    curr = db_conn.cursor()
    curr.execute(sql, node_tuple)

    db_conn.commit()
    db_conn.close()