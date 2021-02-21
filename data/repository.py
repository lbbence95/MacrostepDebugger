# Represent database queries

from data import db as mstep_db

def Initialize_db():
    """Initializes a new database.
    """
    mstep_db.Initialize_db()

#Create
#Create infrastructure
def Register_infrastructure(infra_id, infra_name, registered_timestamp):
    """Register an infrastructure.

    Args:
        infra_id (string): An infrastructure ID.
        infra_name (string): An infrastructure name.
        registered_timestamp (datetime): A timestamp indicating the time of the creation.
    """
    mstep_db.Register_infrastructure(infra_id, infra_name, registered_timestamp)

# Create node
def Register_node(infra_id, node_id, node_name, registered_timestamp, bp_id, public_ip):
    """Register a node.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.
        node_name (string): A node name
        registered_timestamp (datetime): A timestamp indicating the time of the creation.
        bp_id (int): A breakpoint number.
        public_ip (string): An IP address.
    """
    mstep_db.Register_node(infra_id, node_id, node_name, registered_timestamp, bp_id, public_ip)

# Create breakpoint
def Register_breakpoint(infra_id, node_id, registered_timestamp, bp_id, node_data, bp_tag):
    """Register a breakpoint.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.
        registered_timestamp (datetime): A timestamp indicating the time of the creation.
        bp_id (int): A breakpoint number.
        node_data (string): A JSON string containing the details of the breakpoint.
        bp_tag (string): A list of tags in one string.
    """
    mstep_db.Register_breakpoint(infra_id, node_id, registered_timestamp, bp_id, node_data, bp_tag)

# Create tracking table entry
def Register_track_entry(app_name, infra_id, curr_coll_BP_ID):
    """Registers an application-infrastructure pair.

    Args:
        app_name (string): An application name.
        infra_id (string): An infrastructure ID.
        curr_coll_BP_ID (string): The current collective breakpoints ID.
    """

    mstep_db.Register_track_entry(app_name, infra_id, curr_coll_BP_ID)

#Read
#Read single infrastructure
def Read_infrastructure(infra_id):
    """Reads a single infrastructure.

    Args:
        infra_id (string): An infrastructure ID.

    Returns:
        list: A list of infrastructures.
    """

    infras = list(filter(lambda i: i[0] == infra_id, mstep_db.Read_infrastructures()))
    return infras

#Read all infrastructures
def Read_all_infrastructures():
    """Read all infrastructures.

    Returns:
        list: A list of infrastructures.
    """

    return mstep_db.Read_infrastructures()

#Read all infrastructure IDs
def Read_all_infrastructure_ids():
    """Reads all infrastructure IDs

    Returns:
        list: A list of infrastructure IDs.
    """

    infra_ids = list([i[0] for i in Read_all_infrastructures()])
    return infra_ids

#Read single node
def Read_node(infra_id, node_id):
    """Reads the details of a single node.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.

    Returns:
        list: A list of nodes.
    """

    nodes = list(filter(lambda i: i[0] == infra_id and i[1] == node_id, mstep_db.Read_nodes()))
    return nodes

#Read all nodes
def Read_all_nodes():
    """Read all nodes.

    Returns:
        list: A list of nodes.
    """

    return mstep_db.Read_nodes()

#Read nodes from given infrastructure
def Read_nodes_from_infra(infra_id):
    """Read nodes from a given infrastructure.

    Args:
        infra_id (string): An infrastructure ID.

    Returns:
        list: A list of nodes.
    """
    return list(filter(lambda i: i[0] == infra_id, mstep_db.Read_nodes()))

#Read all node IDs from a given infrastructure
def Read_node_ids_from_infra(infra_id):
    """Reads all node IDs from a given infrastructure.

    Args:
        infra_id (string): An infrastructure ID.

    Returns:
        list: A list of node IDs.
    """
    node_ids = list([i[1] for i in Read_nodes_from_infra(infra_id)])
    return node_ids

#Read node ID from given node name in given infra
def Read_node_id_from_node_name(infra_id, node_name):
    """Returns the node ID of the node with the given node name in the given infrastructure.

    Args:
        infra_id (string): An infrastructure ID.
        node_name (string): A node name.

    Returns:
        string: A node ID.
    """
    return str(list(filter(lambda i: i[0] == infra_id and i[2] == node_name, mstep_db.Read_nodes()))[0][1])

#Read a single breakpoint
def Read_breakpoint(infra_id, node_id):
    """Read the breakpoints of a single node.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.

    Returns:
        list: A list of the given node's breakpoints.
    """
    breakpoints = list(filter(lambda i: i[0] == infra_id and i[1] == node_id, mstep_db.Read_breakpoints()))
    return breakpoints

#Read all entry from the tracking table
def Read_all_trace_entry():
    """Read all records from the tracking table.

    Returns:
        list: A list of tuples.
    """   
    return mstep_db.Read_track_table()

#Read one entrys from the tracking table
def Read_one_trace_entry(infra_id):
    """Reads one record from the tracking table.

    Args:
        infra_id (str): An infrastructure ID.

    Returns:
        list: A list of tuples.
    """
    track_pair = list(filter(lambda  i: i[1] == infra_id, mstep_db.Read_track_table()))
    return track_pair

#Read node current breakpoint
def Get_bp_id_for_node(infra_id, node_id):

    return int(list(filter(lambda i: i[0] == infra_id and i[1] == node_id, mstep_db.Read_nodes()))[0][4])

#Update
#Update node breakpoint
def Update_node_at_breakpoint(infra_id, node_id):
    """Updates a given node's current breakpoint and it's permission to move to the next breakpoint.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.
    """
    node_tuple = (infra_id, node_id)
    mstep_db.Update_node_at_new_breakpoint(node_tuple)

#Update node permission
def Update_node_step_permission(infra_id, node_id):
    """Updates a given node's permission to move to the next breakpoint to true.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.
    """

    node_tuple = (infra_id, node_id)
    mstep_db.Update_node_permission(node_tuple)

#Update tracking table entry's current collective breakpoint
def Update_track_table_entry_current_coll_bp(infra_id, curr_coll_BP_ID):
    """Updates a given infrastructure's current collective breakpoint to the given collective breakpoint.

    Args:
        infra_id (str): An infrastructure ID.
        curr_coll_BP_ID (str): A collective breakpoint ID.
    """

    track_tuple = (curr_coll_BP_ID, infra_id)
    mstep_db.Update_tracking_table_entry_current_coll_bp(track_tuple)

#Delete
def Remove_infra_app(infra_id):
    """Deletes an entry with the givenfrom the tracking table.

    Args:
        infra_id (str): An infrastructure ID.
    """

    track_tuple = (infra_id,)
    mstep_db.Remove_tracking_table_entry(track_tuple)