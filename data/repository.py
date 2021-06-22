# Represent database queries

import data.db as mstep_db
from datetime import datetime
from collections import defaultdict
import os.path

def Initialize_db():
    """Initializes a new database.
    """
    mstep_db.Initialize_db()

# Create
# Register new application
def Register_new_application(app_data):
    """Registers a new application with the given name.

    Args:
        app_data (dict): A dictionary containing necessary keys and values.
    """

    new_app = mstep_db.Application()
    new_app.app_name = app_data['app_name']
    new_app.infra_file = os.path.join('infra_defs', app_data['infra_file'])
    new_app.orch = app_data['orch'].lower()
    new_app.orch_loc = app_data['orch_uri']
    new_app.processes = app_data['processes']
    new_app.creation_date = datetime.now()
    mstep_db.Register_application(new_app)

# Register new infrastructure
def Register_new_infrastructure(app_name, infra_id):
    """Registers a new infrastructure.

    Args:
        app_name (string): An application name.
        infra_id (string): An infrastructure ID.
    """

    new_infra = mstep_db.Infrastructure()
    new_infra.app_name = app_name
    new_infra.infra_id = infra_id
    new_infra.registration_date = datetime.now()
    mstep_db.Register_infrastructure(new_infra)

# Register new node
def Register_new_node(infra_id, node_id, node_name, curr_time, bp_id, public_ip):
    """Registers a new node.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.
        node_name (string): A node name
        curr_time (datetime): The current datetime.
        bp_id (int): The current breakpoint the node is at.
        public_ip (string): The public IP-address of the node.
    """

    new_node = mstep_db.Node()
    new_node.infra_id = infra_id
    new_node.node_id = node_id
    new_node.node_name = node_name
    new_node.registered = curr_time
    new_node.curr_bp = bp_id
    new_node.public_ip = public_ip
    mstep_db.Register_node(new_node)

# Register new breakpoint
def Register_new_breakpoint(infra_id, node_id, curr_time, bp_id, bp_data, bp_tag):
    """Registers a new breakpoint.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.
        curr_time (datetime): The current datetime.
        bp_id (int): The current breakpoint the node is at.
        bp_data (string): The received breakpoint informations in JSON.
        bp_tag (string): A list of tags.
    """

    new_bp = mstep_db.Breakpoint()
    new_bp.infra_id = infra_id
    new_bp.node_id = node_id
    new_bp.bp_reg = curr_time
    new_bp.bp_num = bp_id
    new_bp.bp_data = bp_data
    new_bp.bp_tag = bp_tag
    mstep_db.Register_breakpoint(new_bp)


# Read
# Read all applications
def Read_all_application():
    """Reads all applications from the database.

    Returns:
        list: A list of Applications.
    """

    return mstep_db.Read_all_application()

# Read single application
def Read_given_application(app_name):
    """Reads an application with the given app_name.

    Args:
        app_name (string): An application name.

    Returns:
        Application: An Application fulfilling the condition. None if no such entry found.
    """
    application = list(filter(lambda x: x.app_name == app_name, mstep_db.Read_all_application()))
    
    if (len(application) != 0):
        return application[0]
    else:
        return None

#Read all infrastructure
def Read_all_infrastructure():
    """Reads all infrastructures.

    Returns:
        list: A list of Infrastructures.
    """

    return mstep_db.Read_all_infrastructure()

# Read all instance for given application
def Read_all_instance_for_given_application(app_name):
    """Reads all isntance of the given application.

    Args:
        app_name (string): An application name

    Returns:
        lsit: A list of Infrastructures. None if no such entry found.
    """

    instances = list(filter(lambda x: x.app_name == app_name, mstep_db.Read_all_infrastructure()))

    if (len(instances) != 0):
        return instances
    else:
        return None


# Read single infrastructure
def Read_given_infrastructure(infra_id):
    """Reads an infrastructure with the given infra_id.

    Args:
        infra_id (string): An infrastructure id.

    Returns:
        Infrastructure: An Infrastructure fulfilling the condition. None if no such entry found.
    """

    infrastructure = list(filter(lambda x: x.infra_id == infra_id, mstep_db.Read_all_infrastructure()))
    if (len(infrastructure) != 0):
        return infrastructure[0]
    else:
        return None

# Read all nodes
def Read_all_node():
    """Reads all nodes from the database.

    Returns:
        list: A list of Nodes.
    """

    return mstep_db.Read_all_node()

# Read all nodes of an infrastructure
def Read_nodes_from_infra(infra_id):
    """Read nodes from a given infrastructure.

    Args:
        infra_id (string): An infrastructure ID.

    Returns:
        list: A list of nodes ordered by node_id.
    """

    nodes = list(filter(lambda x: x.infra_id == infra_id, mstep_db.Read_all_node()))

    if (len(nodes) != 0):
        return sorted(nodes, key=lambda x: (x.node_name, x.node_id), reverse=False)
    else:
        return None

# Read single node
def Read_given_node(infra_id, node_id):
    """Reads a Node with the given infra_id and node_id.

    Args:
        infra_id (string): An infrastructure id.
        node_id (string): A node id.

    Returns:
        Node: A Node fulfilling the conditions. None if no such entry found.
    """

    node = list(filter(lambda x: x.infra_id == infra_id and x.node_id == node_id, mstep_db.Read_all_node()))
    if(len(node) != 0):
        return node[0]
    else:
        return None

# Read all breakpoint
def Read_all_breakpoint():
    """Reads all breakpoints from the database.

    Returns:
        list: A list of Breakpoints.
    """

    return mstep_db.Read_all_breakpoint()

# Read breakpoints of node
def Read_given_nodes_breakpoint(infra_id, node_id):
    """Reads the breakpoints of a given node.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.

    Returns:
        lsit: A list of Breakpoints.
    """

    bp = list(filter(lambda x: x.infra_id and x.node_id == node_id, mstep_db.Read_all_breakpoint()))
    return bp

#Read node current breakpoint
def Read_current_bp_num_for_node(infra_id, node_id):
    """Reads the current breakpoint number for the given node.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.

    Returns:
        int: An integer which is the current breakpoint number for the given node (e.g. 2).
    """

    return int(list(filter(lambda x: x.infra_id and x.node_id == node_id, mstep_db.Read_all_node()))[0].curr_bp)

# Update
# Update application root collective breakpoint
def Update_app_root_collective_breakpoint(app_name, root_id):
    """Updates an application's root collective breakpoint.

    Args:
        app_name (string): An application name.
        root_id (string): UUID of the new root.
    """

    mstep_db.Update_app_root_collective_breakpoint(app_name, root_id)

# Update application current collective breakpoint
def Update_app_current_collective_breakpoint(app_name, coll_bp_id):
    """Updates an application's current collective breakpoint.

    Args:
        app_name (string): An application name.
        coll_bp_id (string): A collective breakpoint ID.
    """

    mstep_db.Update_app_current_collective_breakpoint(app_name, coll_bp_id)

# Update infrastructure name 
def Update_infrastructure_name(infra_id ,new_infra_name):
    """Updates an existing infrastructure's name.

    Args:
        infra_id (string): An infrastructure ID.
        new_infra_name (string): An infrastucture name.
    """
    
    mstep_db.Update_infrastructure_name(infra_id, new_infra_name)

#Update infrastructure current collective breakpoint
def Update_instance_current_collective_breakpoint(infra_id, coll_bp_id):
    """Updates the given infrastructure's current collective breakpoint to the given collective breakpoint ID.

    Args:
        infra_id (string): An infrastructure ID.
        coll_bp_id (string): A collective breakpoint ID.
    """

    mstep_db.Update_instance_current_collective_breakpoint(infra_id, coll_bp_id)

#Update node permission
def Update_node_step_permission(infra_id, node_id):
    """Updates a given node's step permission to true.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.
    """

    mstep_db.Update_node_permission(infra_id, node_id)

#Update node breakpoint
def Update_node_current_bp_and_permission(infra_id, node_id):
    """Updates a given node's current breakpoint and it's permission to move to the next breakpoint.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.
    """

    mstep_db.Update_node_current_bp_and_permission(infra_id, node_id)

#Update node to finished status
def Update_node_status_finished(infra_id, node_id):
    """Updates the given node's status as finished, meaning no more breakpoints exist for the node.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.
    """

    mstep_db.Update_node_status_finished(infra_id, node_id)

# Other
def Infra_exists(infra_id):
    """Decides if the given infrastructure already exists.

    Args:
        infra_id (string): An infrastructure ID.

    Returns:
        boolean: True if the infrastructure exists, False if not.
    """

    infras = Read_given_infrastructure(infra_id)

    if (infras != None):
        return True
    else:
        return False

def App_exists(app_name):
    """Decides if the given application already exists or not.

    Args:
        app_name (string): An application name.

    Returns:
        boolean: True if the application exists, False if not.
    """

    apps = Read_given_application(app_name)
    
    if (apps == None):
        return False
    else:
        return True

def Node_exists(infra_id, node_id):
    """Checks if the given node within the given infrastructure exists or not.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.

    Returns:
        bool: True if the node exists in the given infrastructure, False if not.
    """

    nodes = Read_given_node(infra_id, node_id)

    if (nodes != None):
        return True
    else:
        return False

def Has_infra_finished(infra_id):
    """Check if the processes in the given infrastructure instance had already finished or not.

    Args:
        infra_id (string): An infrastructure ID.

    Returns:
        bool: True if every process has finished, otherwise False.
    """

    nodes = Read_nodes_from_infra(infra_id)

    if (nodes != None):

        for act_node in nodes:
            if (act_node.finished == 0):
                return False
        return True
    else:
        return False

def Is_node_permission_true(infra_id, node_id):
    """Decides if the given node in the given infrastructure is permitted to move to the next breakpoint.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.

    Returns:
        bool: True if the node is permited, False if not.
    """

    node = Read_given_node(infra_id, node_id)

    if (node.move_next == 1):
        return True
    else:
        return False

def Is_infra_in_consistent_global_state(infra_id):
    """Checks if the given infrastructure is in a consistent global state or not.

    Args:
        infra_id (string): An infrastructure ID.
    
    Returns:
        bool: True if the given infrastructure is in a consistent global state, otherwise False.
    """

    cons_global_state = True
    infra_nodes = Read_nodes_from_infra(infra_id)

    if (len(infra_nodes) == 0):
        cons_global_state = False
    else:
        for act_node in infra_nodes:
            if (act_node.move_next != 0):
                cons_global_state = False
                break
 
    return cons_global_state

def Is_infra_in_root_state(infra_id):
    """Checks if the given infrastructure is in a root state or not.

    Args:
        infra_id (string): An infrastructure ID.
    """
    
    # An infrastructure is in a root state if every process is waiting for permission (processes are halted) and every process is at their first breakpoint.
    if (Is_infra_in_consistent_global_state(infra_id) == True):
        
        # Check if every process is at its first breakpoint
        infra_nodes = Read_nodes_from_infra(infra_id)
        root_state = True

        if (len(infra_nodes) == 0):
            root_state = False
        else:
            for act_node in infra_nodes:
                if (act_node.curr_bp != 1):
                    root_state = False
                    break
        
        return root_state
    else:
        return False

def Get_global_state_for_infra(infra_id):
    """Gets the global state for the given infrastructure.

    Args:
        infra_id (string): An infrastructure ID.

    Returns:
        [type]: [description]
    """

    node_states = defaultdict(list)

    nodes = Read_nodes_from_infra(infra_id) 

    for act_node in nodes:
        node_states[act_node.node_name].append(act_node.curr_bp)
    
    dict(node_states)

    return dict(sorted(node_states.items(), reverse=False))

def How_many_processes_havent_finished(instance_id):
    """Returns the number of unfinished processes in the given instance.

    Args:
        instance_id (string): An application instance (infrastructure) ID.

    Returns:
        int: The number of unifished processes.
    """

    processes = Read_nodes_from_infra(instance_id)

    num_unfinished = 0

    for act_proc in processes:
        if (act_proc.finished == 0):
            num_unfinished += 1
    
    return num_unfinished