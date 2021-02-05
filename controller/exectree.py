# Module to handle Neo4j transactions, execution-tree operations

from data import repository as mstep_repo
from py2neo import Graph, Node, Relationship, NodeMatcher, NodeMatch
from time import strftime
import datetime, uuid, json, logging

#Logger setup
logger = logging.getLogger('exectree')
logger.propagate = False
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
formatter = logging.Formatter('*** (%(asctime)s): %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def Infra_app_pair_root(infra_id, app_name):
    """Processes an infrastructure-application pair. Check if the given infrastructure is in root state.

    Args:
        infra_id (string): An infrastructure ID.
        app_name (string): An application name.

    Returns:
        tuple: A bool and a string. If the process succeded, the bool is True. Otherwise False. String is a description message.
    """
    
    # Check if pairing already exists
    app_infra_pair = mstep_repo.Read_one_trace_entry(infra_id)

    if (len(app_infra_pair) > 0):
        return (False, 'Infrastructure is already traced.')
    
    # Check root state
    if (Is_root_state(infra_id) == True):
        #Check Neo4j database connection
        conn_details = Read_connection_details()
        
        if (conn_details[0] == False):
            return (False, 'Please check Neo4j configuration file.')
        
        # Get root node
        neo_graph = conn_details[1]
        node_matcher = NodeMatcher(neo_graph)
        root_node = node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.node_type =~ '{}'".format(app_name, "root")).first()

        # Check if there is a root. None means it does not exist
        if root_node != None:
            mstep_repo.Register_track_entry(app_name, infra_id, root_node['coll_bp_id'])
            return (True, 'Root node already exists. No root created. Tracking infrastructure "{}".'.format(infra_id))
        else:
            logger.info('Root does not exist. Creating root collective breakpoint.')

            # Gather infrastructure state data
            root_node_bp_id = str(uuid.uuid4())
            process_states = Get_node_states(infra_id)
            prev_coll_bp_ID = "none"

            transact = neo_graph.begin()

            # Create root node
            root_node = Node("Collective_BP", app_name=app_name, infra_id=infra_id, node_type="root", prev_coll_bp=prev_coll_bp_ID, coll_bp_id=root_node_bp_id, process_states=json.dumps(process_states))
            transact.create(root_node)

            # Send Neo4j data
            transact.commit()

            # Store the infra-app pair as tracked
            mstep_repo.Register_track_entry(app_name, infra_id, root_node_bp_id)

            logger.info('Transaction sent! (Application name: "{}", infrastructure: "{}" paired)'.format(app_name, infra_id))
            return ( True, 'Infrastructure "{}" was in root state. Root node and pairing created.'.format(infra_id) )
    else:
        return ( False, 'Current state is not a valid root state. Make sure every node is at its first breakpoint, and no node is permitted.' )

def Send_collective_breakpoint(infra_id):
    """Stores a collective breakpoint at the predefined Neo4j database.

    Args:
        infra_id (string): An infrastructure ID.
    
    Returns:
        tuple: A boolean indicating if the operation was successful and a string message.
    """

    # Check if global state is consistent and not a root (every node is waiting)
    if ((Is_root_state(infra_id) == False) and (Is_consistent_global_state(infra_id) == True)):
        # Check Neo4j connection
        conn_details = Read_connection_details()
        if (conn_details[0] == False):
            return (False, 'Connection error. Please check Neo4j configuration file.')

        # Get previous node
        tracked_pair = mstep_repo.Read_one_trace_entry(infra_id)[0]
        neo_graph = conn_details[1]
        node_matcher = NodeMatcher(neo_graph)

        prev_node = node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.coll_bp_id =~ '{}'".format(tracked_pair[0], tracked_pair[2])).first()

        # Check for none
        if (prev_node != None):
            # Gather data
            coll_bp_id = str(uuid.uuid4())
            process_states = Get_node_states(infra_id)
            prev_coll_bp = tracked_pair[2]

            # Check for existing child node
            child_nodes = list(node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.prev_coll_bp =~ '{}'".format(tracked_pair[0], tracked_pair[2])))

            # Check for children nodes.
            if (len(child_nodes) == 0):
                # No children, create new collective breakpoint
                transact = neo_graph.begin()

                new_node = Node("Collective_BP", app_name=tracked_pair[0], infra_id=infra_id, node_type="other", prev_coll_bp=prev_coll_bp, coll_bp_id=coll_bp_id, process_states=json.dumps(process_states))
                transact.create(new_node)

                coll_bp_rel = Relationship(prev_node, "MACROSTEP", new_node, app_name=tracked_pair[0], infra_id=infra_id)
                transact.create(coll_bp_rel)
                transact.commit()

                # Update current breakpoint field
                mstep_repo.Update_track_table_entry_current_coll_bp(infra_id, coll_bp_id)

                return (True, 'Current state is a new state, new collective breakpoint created.')
            else:
                # There are children nodes, check for equal process state
                for act_node in child_nodes:
                    # Get node state
                    act_state = json.loads(act_node["process_states"])

                    if (act_state == process_states):
                        # Equal process state, store current collective breakpoint ID
                        mstep_repo.Update_track_table_entry_current_coll_bp(infra_id, act_node["coll_bp_id"])
                        return (True, 'Success. Current state already exists, no new collective breakpoint needed.')
                
                # Create new collective breakpoint
                transact = neo_graph.begin()

                new_node = Node("Collective_BP", app_name=tracked_pair[0], infra_id=infra_id, node_type="other", prev_coll_bp=prev_coll_bp, coll_bp_id=coll_bp_id, process_states=json.dumps(process_states))
                transact.create(new_node)

                # Create node relationship
                coll_bp_rel = Relationship(prev_node, "MACROSTEP", new_node, app_name=tracked_pair[0], infra_id=infra_id)
                transact.create(coll_bp_rel)

                transact.commit()

                # Update current breakpoint field in the tracking table
                mstep_repo.Update_track_table_entry_current_coll_bp(infra_id, coll_bp_id)

                return (True, 'Success. Current state is a new state, new collective breakpoint created.')
        else:
            return (False, 'Unexpected error. Node not found.')          
    else:
        return (False, 'Infrastructure "{}" is not in a consistent global state.'.format(infra_id))

def Stop_tracing(infra_id):
    """Stops tracking the given infrastructure.

    Args:
        infra_id (str): An infrastructure ID.
    """
    mstep_repo.Remove_infra_app(infra_id)

#Helper functions and methods
def Is_root_state(infra_id):
    """Checks if the given ifrastructure is in a root state. Meaning every node is at its first breakpoint and they are not permitted to move to the next breakpoint.

    Args:
        infra_id (string): An infrastructure ID.

    Returns:
        boolean: True if the infrastructure is in a root state. False if not.
    """

    root_state = True
    infra_nodes = mstep_repo.Read_nodes_from_infra(infra_id)

    #Check if every node is at the first breakpoint
    for act_node in infra_nodes:
        if ((act_node[4] != 1) or (act_node[5] != 0)):
            root_state = False
            break

    return root_state

def Is_infrastructure_tracked(infra_id):
    """Checks if the given ifrastructure is tracked (traced) or not.

    Args:
        infra_id (string): An infrastructure ID.

    Returns:
        boolean: True if the infrastructure is tracked, False if not.
    """

    app_infra_pair = mstep_repo.Read_one_trace_entry(infra_id)

    if ((len(app_infra_pair) == 1) and (app_infra_pair[0][1] == infra_id)):
        return True
    else:
        return False

def Is_consistent_global_state(infra_id):
    """Checks if the given infrastructure is in a consistent global state.

    Args:
        infra_id (str): An infrastructure ID.
    
    Returns:
        bool: A True boolean if the given infrastructure is in a consistent global state, otherwise False.
    """

    cons_global_state = True
    infra_nodes = mstep_repo.Read_nodes_from_infra(infra_id)

    if (len(infra_nodes) == 0):
        return False

    for act_node in infra_nodes:
        if (act_node[5] != 0):
            cons_global_state = False
            break
    
    return cons_global_state

def Read_connection_details():
    """Reads connection details from the "neo4j_conn.cfg" file.

    Returns:
        tuple: A True boolean and a py2neo Graph object if connection can be established. Otherwise False and None.
    """
    neo_graph = None
    conn_details = {}

    logger.info('Connecting to database...')

    # Check config file
    try:
        with open('controller/neo4j_conn.cfg') as f_cfg:
            for line in f_cfg:
                line = line[:-1]
                (key, val) = line.split('=')
                conn_details[str(key)] = val
    
        neo_graph = Graph(conn_details['host'], user=conn_details['user'], password=conn_details['password'], secure=False)
    except FileNotFoundError:
        logger.error('Configuration file does not exist!')
        return (False, neo_graph)
    except ValueError:
        logger.error('Invalid configuration file!')
        return (False, neo_graph)
    except KeyError:
        logger.error('Invalid configuration file!')
        return (False, neo_graph)
    except Exception:
        logger.info('Connection error!')
        return (False, neo_graph)

    
    # Testing connection
    try:
        neo_graph.run("Match () Return 1 Limit 1")
        logger.info('Connection ok!')
        return (True, neo_graph)
    except Exception:
        print('*** Connection error!')
        return (False, neo_graph)

def Get_node_states(infra_id):
    """Returns a dictionary containing the node's name and its current breakpoint.

    Args:
        infra_id (string): An infrastructure ID.

    Returns:
        dict: A dictionary containing a node name and a breakpoint number.
    """

    node_states = {}

    nodes = mstep_repo.Read_nodes_from_infra(infra_id)

    for act_node in nodes:
        node_states[str(act_node[2])] = str(act_node[4])
    
    return dict(sorted(node_states.items(), key=lambda x: x[0], reverse=False))


def Get_path_to_target_coll_bp(app, coll_bp_id, neo_graph):
    """Gets a route, path to the given collective breakpoint for the given application.

    Args:
        app (str): An application name.
        coll_bp_id (str): A collective breakpoint ID.
        neo_graph (graph): A Neo4j graph
    
    Returns:
        tuple: If the given collective breakpoint exists in the given application, then a list of strings containing the collective breakpoint IDs and a list of global states. Otherwise both returned values are None.
    """

    def Get_path_to_root(app_name, coll_bp_id, path_list, state_list, neo_graph):
        """Gets a collection of collective breakpoint IDs leading from the root node to the given collective breakpoint.

        Args:
            app_name (str): An application name.
            coll_bp_id (str): A collective breakpoint ID.
            path_list (list): A(n empty) list to store the collective breakpoint IDs.
            state_list (list): A(n empty) list to store the states.
            neo_graph (graph): A Neo4j graph.

        Returns:
            tiple: A list of strings containing the collective breakpoint IDs the path contains and a list of string containing the corresponding global states.
        """

        node_matcher = NodeMatcher(neo_graph)

        curr_node = node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.coll_bp_id =~ '{}'".format(app_name, coll_bp_id)).first()
        curr_node_type = curr_node["node_type"]
        curr_node_id = curr_node["coll_bp_id"]
        curr_node_state = curr_node["process_states"]

        if (curr_node_type == 'root'):
            path_list.append(curr_node_id)
            state_list.append(curr_node_state)
        else:
            parent_node_id = curr_node["prev_coll_bp"]
            Get_path_to_root(app_name, parent_node_id, path_list, state_list, neo_graph)
            path_list.append(curr_node_id)
            state_list.append(curr_node_state)
    
        return (path_list, state_list)

    node_matcher = NodeMatcher(neo_graph)
    target_coll_bp = node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.coll_bp_id =~ '{}'".format(app, coll_bp_id)).first()

    if (target_coll_bp == None):
        # None, no such collective breakpoint
        return (None, None)
    else:
        # Not none, target node found
        target_node = Get_path_to_root(app, coll_bp_id, [], [], neo_graph) 

        return (target_node[0], target_node[1])