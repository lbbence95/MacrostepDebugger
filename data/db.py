# Represents the database layer of the application

import sqlite3
import os.path


db_conn = sqlite3.connect(os.path.join('data','mstepDB.db'))

def Initialize_db():
    """Drops tables and initializes a new database file.
    """

    curr = db_conn.cursor()

    # Infrastructures
    # An infrastructure instance is identified its: infrastructure ID (infraID). Also important data is the infrastucture name (infraName).
    # The time when it was registered is also stored (registered).
    curr.execute("""DROP TABLE IF EXISTS Infras""")
    curr.execute("""CREATE TABLE Infras (
        infraID TEXT NOT NULL PRIMARY KEY,
        infraName TEXT,
        registered TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) """)

    # Nodes
    # Nodes currently represent virtual machines (VM).
    curr.execute("""DROP TABLE IF EXISTS Nodes""")
    curr.execute("""CREATE TABLE Nodes (
        infraID TEXT NOT NULL,
        nodeID TEXT NOT NULL,
        nodeName TEXT,
        nodeRegistered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        currBP INTEGER DEFAULT 0,
        moveNext INTEGER DEFAULT 0,
        publicIP TEXT DEFAULT 'n/a',
        PRIMARY KEY (infraID, nodeID),
        FOREIGN KEY (infraID) REFERENCES Infras (infraID)
    ) """)

    # Breakpoints
    curr.execute("""DROP TABLE IF EXISTS Breakpoints""")
    curr.execute("""CREATE TABLE Breakpoints (
        infraID TEXT NOT NULL,
        nodeID TEXT NOT NULL,
        bpRegistered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        bpNum INTEGER,
        nodeData TEXT,
        bpTag TEXT DEFAULT "",
        PRIMARY KEY (infraID, nodeID, bpNum),
        FOREIGN KEY (infraID) REFERENCES Infras (infraID),
        FOREIGN KEY (nodeID) REFERENCES Nodes (nodeID)
    )""")

    # Tracking table
    curr.execute("""DROP TABLE IF EXISTS Tracking""")
    curr.execute("""CREATE TABLE Tracking (
        app_name TEXT NOT NULL,
        infraID TEXT NOT NULL,
        curr_coll_BP_ID TEXT NOT NULL,
        PRIMARY KEY (app_name, infraID),
        FOREIGN KEY (infraID) REFERENCES Infras (infraID)
    )""")

    db_conn.commit()
    db_conn.close()

#Create
#Create infrastructure
def Register_infrastructure(infra_id, infra_name, registered_timestamp):
    """Creates a new infrastructure entry in the database.

    Args:
        infra_id (string): An infrastructure ID.
        infra_name (string): The infrastructures name.
        registered_timestamp (datetime): A timestamp stating the date and time of the registration.
    """

    infra_tuple = (infra_id, infra_name, registered_timestamp)

    db_conn = sqlite3.connect(os.path.join('data','mstepDB.db'), detect_types=sqlite3.PARSE_DECLTYPES)

    curr = db_conn.cursor()
    curr.execute('''INSERT INTO Infras (infraID, infraName, registered) VALUES (?,?,?)''', infra_tuple)
    
    db_conn.commit()
    db_conn.close()

#Create node
def Register_node(infra_id, node_id, node_name, registered_timestamp, bp_id, public_ip):
    """Creates a new node entry in the database.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node id.
        node_name (string): The name of the node.
        registered_timestamp (datetime): A timestamp stating the date and time of the registration.
        bp_id (int): The current breakpoint.
        public_ip (string): The public IP address of the node.
    """

    node_tuple = (infra_id, node_id, node_name, registered_timestamp, bp_id, public_ip)

    db_conn = sqlite3.connect(os.path.join('data','mstepDB.db'), detect_types=sqlite3.PARSE_DECLTYPES)
    
    curr = db_conn.cursor()
    curr.execute('''INSERT INTO Nodes (infraID, nodeID, nodeName, nodeRegistered, currBP, publicIP) VALUES (?,?,?,?,?,?)''', node_tuple)
    
    db_conn.commit()
    db_conn.close()

#Create breakpoint
def Register_breakpoint(infra_id, node_id, registered_timestamp, bp_id, node_data, bp_tag):
    """Creates a new breakpoint entry.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.
        registered_timestamp (datetime): A timestamp stating the date and time of the registration.
        bp_id (int): The current breakpoint.
        node_data (string): A JSON string containing the breakpoint.
        bp_tag (string): A description of the breakpoint (e.g.: tags).
    """

    bp_tuple = (infra_id, node_id, registered_timestamp, bp_id, node_data, bp_tag)

    db_conn = sqlite3.connect(os.path.join('data','mstepDB.db'), detect_types=sqlite3.PARSE_DECLTYPES)

    curr = db_conn.cursor()
    curr.execute('''INSERT INTO Breakpoints (infraID, nodeID, bpRegistered, bpNum, nodeData, bpTag) VALUES (?,?,?,?,?,?)''', bp_tuple)
    
    db_conn.commit()
    db_conn.close()

#Create tracking table entry
def Register_track_entry(app_name, infra_id, curr_coll_BP_ID):
    """Creates a new application-infrastructure entry.

    Args:
        app_name (string): An application name.
        infra_id (string): An infrastructure ID.
        curr_coll_BP_ID (string): The current collective breakpoints ID.
    """

    track_tuple = (app_name, infra_id, curr_coll_BP_ID)

    db_conn = sqlite3.connect(os.path.join('data','mstepDB.db'), detect_types=sqlite3.PARSE_DECLTYPES)

    curr = db_conn.cursor()
    curr.execute('''INSERT INTO Tracking (app_name, infraID, curr_coll_BP_ID) VALUES (?,?,?)''', track_tuple)

    db_conn.commit()
    db_conn.close()

#Read
#Read all infrastructures
def Read_infrastructures():
    """Reads the details of all infrastructures.

    Args:
        sql (string): Represents an SQL expression.

    Returns:
        list: A list of of tuples containing infrastructure data.
    """

    db_conn = sqlite3.connect(os.path.join('data','mstepDB.db'))

    cur = db_conn.cursor()
    cur.execute('''SELECT * FROM Infras''')

    result = cur.fetchall()

    db_conn.commit()
    db_conn.close()

    return result

#Read all nodes
def Read_nodes():
    """Reads the details of managed nodes.

    Returns:
        list: A list of nodes (as a tuple).
    """

    db_conn = sqlite3.connect(os.path.join('data','mstepDB.db'))

    cur = db_conn.cursor()
    cur.execute('''SELECT * FROM Nodes''')

    result = cur.fetchall()

    db_conn.commit()
    db_conn.close()

    return result

#Read all breakpoints
def Read_breakpoints():
    """Reads the details of managed nodes.

    Returns:
        list: A list of tuple containing breakpoint data.
    """

    db_conn = sqlite3.connect(os.path.join('data','mstepDB.db'))

    cur = db_conn.cursor()
    cur.execute('''SELECT * FROM Breakpoints''')

    result = cur.fetchall()

    db_conn.commit()
    db_conn.close()

    return result

#Read all track table entry
def Read_track_table():
    """Reads all tracking table entry from the database.

    Returns:
        list: A list of tuples.
    """

    db_conn = sqlite3.connect(os.path.join('data','mstepDB.db'))

    cur = db_conn.cursor()
    cur.execute('''SELECT * FROM Tracking''')

    result = cur.fetchall()

    db_conn.commit()
    db_conn.close()

    return result

#Update
#Update node breakpoint
def Update_node_at_new_breakpoint(node_tuple):
    """Updates a given nodes breakpoint and.

    Args:
        node_tuple (tuple): A set of data to be substituted into the SQL statement.
    """

    db_conn = sqlite3.connect(os.path.join('data','mstepDB.db'))

    curr = db_conn.cursor()
    curr.execute('''UPDATE Nodes SET currBP = currBP + 1, moveNext = 0 WHERE infraID=(?) AND nodeID=(?)''', node_tuple)

    db_conn.commit()
    db_conn.close()

#Update node permission
def Update_node_permission(node_tuple):
    """Updates a given node's step permission.

    Args:
        node_tuple (tuple): A set of data to be substituted into the SQL statement.
    """

    db_conn = sqlite3.connect(os.path.join('data','mstepDB.db'))

    curr = db_conn.cursor()
    curr.execute('''UPDATE Nodes SET moveNext = 1 WHERE infraID=(?) AND nodeID=(?)''', node_tuple)

    db_conn.commit()
    db_conn.close()

#Update current collective breakpoint
def Update_tracking_table_entry_current_coll_bp(track_tuple):
    """Updates a tracking table entry's current collective breakpoint.

    Args:
        track_tuple (tuple): Must contain a collective breakpoint ID, and an infrastructure ID.
    """

    db_conn = sqlite3.connect(os.path.join('data','mstepDB.db'))

    curr = db_conn.cursor()
    curr.execute('''UPDATE Tracking SET curr_coll_BP_ID = (?) WHERE infraID = (?)''', track_tuple)

    db_conn.commit()
    db_conn.close()

#Delete
#Delete a tracking table entry
def Remove_tracking_table_entry(track_tuple):
    """Deletes a tracking table entry.

    Args:
        track_tuple (tuple): A set of data to be substituted into the SQL statement.
    """

    db_conn = sqlite3.connect(os.path.join('data','mstepDB.db'))

    curr = db_conn.cursor()
    curr.execute('''DELETE FROM Tracking WHERE infraID = (?)''', track_tuple)

    db_conn.commit()
    db_conn.close()