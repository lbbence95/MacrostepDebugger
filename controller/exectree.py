# Module to handle Neo4j transactions, execution-tree operations

from py2neo.database import work
import data.repository as mstep_repo
from py2neo import Graph, Node, Relationship, NodeMatcher
import uuid, json, logging, os.path, yaml

#Logger setup
logger = logging.getLogger('exectree')
logger.propagate = False
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
formatter = logging.Formatter('*** (%(asctime)s): %(message)s', "%Y-%m-%d %H:%M:%S")
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)


def Read_connection_details(silent=False):
    """Reads connection details from 'controller/neo4j_conn.yaml'.

    Args:
        silent (bool, optional): Suppress console messages if conenction is OK. Defaults to False.

    Returns:
        tuple: A True boolean and a py2neo Graph object if connection can be established. Otherwise a False boolean and None.
    """

    neo_graph = None
    conn_details = {}

    try:
        neo4j_cfg = yaml.safe_load(open(os.path.join('controller','neo4j_conn.yaml')))

        conn_details['host'] = neo4j_cfg['host'] 
        conn_details['user'] = neo4j_cfg['user']
        conn_details['password'] = neo4j_cfg['password']

        neo_graph = Graph(conn_details['host'], user=conn_details['user'], password=conn_details['password'], secure=False)
        if (silent == False):
            logger.info('Connecting to Neo4j database...')

        neo_graph.run("Match () Return 1 Limit 1")

        if (silent == False):
            logger.info('Connection ok!')

        return (True, neo_graph)
    except FileNotFoundError:
        logger.error('Configuration file not found!')
        return (False, None)
    except (ValueError, KeyError, TypeError):
        logger.error('Invalid configuration file!')
        return (False, None)
    except Exception:
        logger.error('Connection error!')
        return (False, None)     


def Create_root(app, infra_id, process_states):
    """Creates a root collective breakpoint for the given application.

    Args:
        app (Application): An Application instance.
        infra_id (string): An infrastructure ID.
        process_states:

    Returns:
        string: A UUID in string, the root collective breakpoint.
    """

    conn_details = Read_connection_details(silent=True)
    neo_graph = conn_details[1]
 
    root_id = str(uuid.uuid4())

    # Create root node
    transact = neo_graph.begin()

    root_node = Node("Collective_BP", app_name=app.app_name, infra_id=infra_id, node_type="root", prev_coll_bp="", exhausted="No", coll_bp_id=root_id, process_states=json.dumps(process_states))

    transact.create(root_node)

    # Commit
    transact.commit()

    return root_id


def Create_collective_breakpoint(app, app_instance, process_states):
    """Inserts a new collective breakpoint into the application's execution tree.

    Args:
        app (Application): An Application.
        app_instance (Infrastructure): An application instance (Infrastructure).
        process_states (dict): A dictionary defining the state of each process in the instance.

    Returns:
        str: The newly created collective breakpoints ID.
    """

    conn_details = Read_connection_details(silent=True)
    neo_graph = conn_details[1]
    node_matcher = NodeMatcher(neo_graph)

    # Create new node
    transact = neo_graph.begin()
    new_node = None
    coll_bp_id = str(uuid.uuid4())

    not_finished = mstep_repo.How_many_processes_havent_finished(app_instance.infra_id)

    if (not_finished == 0):
        new_node = Node("Collective_BP", app_name=app.app_name, infra_id=app_instance.infra_id, node_type="final", prev_coll_bp=app_instance.curr_coll_bp, exhausted="Yes", coll_bp_id=coll_bp_id, process_states=json.dumps(process_states))
    elif (not_finished >= 2):
        new_node = Node("Collective_BP", app_name=app.app_name, infra_id=app_instance.infra_id, node_type="alternative", prev_coll_bp=app_instance.curr_coll_bp, exhausted="No", coll_bp_id=coll_bp_id, process_states=json.dumps(process_states))
    elif (not_finished == 1):
        new_node = Node("Collective_BP", app_name=app.app_name, infra_id=app_instance.infra_id, node_type="deterministic", prev_coll_bp=app_instance.curr_coll_bp, exhausted="Yes", coll_bp_id=coll_bp_id, process_states=json.dumps(process_states))

    transact.create(new_node)

    prev_node = node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.coll_bp_id =~ '{}'".format(app.app_name, app_instance.curr_coll_bp)).first()  
    
    prev_proc_states = json.loads(prev_node['process_states'])
    curr_proc_states = json.loads(new_node['process_states'])
    process_stepped = ""

    i: int
    for act_proc_name in curr_proc_states:      
        i = 0
        while (i < len(curr_proc_states[act_proc_name])):
            if (curr_proc_states[act_proc_name][i] != prev_proc_states[act_proc_name][i]):
                process_stepped = act_proc_name
                break
            i += 1
        if (process_stepped != ""):
            break

    coll_bp_rel = Relationship(prev_node, "MACROSTEP", new_node, app_name=app.app_name, infra_id=app_instance.infra_id, process_stepped="{}[{}]".format(process_stepped, i + 1))
    transact.create(coll_bp_rel)

    transact.commit()
    
    return coll_bp_id


def Get_closest_non_exhausted_parent(app, curr_bp_id, final_process_states):
    """Returns the closest non-exhausted parent node.

    Args:
        app (Application): An Application.
        curr_bp_id (str): A collective breakpoint ID to start search from.
        final_process_states (dict): A dictionary containing the final state of processes.

    Returns:
        str: The closest non-exhausted collective breakpoint's ID. If even root is exhausted, then an empty string ("").
    """


    # Get Neo4j connection details
    conn_details = Read_connection_details(silent=True)
    neo_graph = conn_details[1]
    node_matcher = NodeMatcher(neo_graph)

    # Get previous collective breakpoint
    curr_coll_bp = node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.coll_bp_id =~ '{}'".format(app.app_name, curr_bp_id)).first()
    curr_coll_bp = node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.coll_bp_id =~ '{}'".format(app.app_name, curr_coll_bp['prev_coll_bp'])).first()

    not_exhausted = False
    if (curr_coll_bp['exhausted'] == "No"):
        not_exhausted = True
    
    # Go backwards in tree until a non-exhausted node is found
    while (not_exhausted != True):

        if (curr_coll_bp['node_type'] == "root"):
            if (curr_coll_bp['exhausted'] == "Yes"):
                return ""
        else:
            curr_coll_bp = node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.coll_bp_id =~ '{}'".format(app.app_name, curr_coll_bp['prev_coll_bp'])).first()
        
        if (curr_coll_bp['exhausted'] == "No"):
            return curr_coll_bp['coll_bp_id']
    

def Update_closest_alternative_coll_bp(app, curr_bp_id, final_process_states):
    """Updates the closest alternative parent collective breakpoint to exhausted if every possible execution path has been traversed from that collective breakpoint.

    Args:
        app (Application): An Application.
        curr_bp_id (string): A collective breakpoint ID.
        final_process_states (dict): A (default)dict describing the final state of processes.
    """

    # Get Neo4j connection details
    conn_details = Read_connection_details(silent=True)
    neo_graph = conn_details[1]
    node_matcher = NodeMatcher(neo_graph)

    # Get previous collective breakpoint
    curr_coll_bp = node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.coll_bp_id =~ '{}'".format(app.app_name, curr_bp_id)).first()
    curr_coll_bp = node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.coll_bp_id =~ '{}'".format(app.app_name, curr_coll_bp['prev_coll_bp'])).first()

    is_root_or_alt = False
    if (curr_coll_bp['node_type'] == "root" or curr_coll_bp['node_type'] == "alternative"):
        is_root_or_alt = True

    # Go backwards in tree until an alternative coll. bp. is found
    while (is_root_or_alt == False):
        curr_coll_bp = node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.coll_bp_id =~ '{}'".format(app.app_name, curr_coll_bp['prev_coll_bp'])).first()
        if (curr_coll_bp['node_type'] == "root" or curr_coll_bp['node_type'] == "alternative"):
            is_root_or_alt = True
        
    alternative_processes = json.loads(curr_coll_bp['process_states'])
    final_state_processes = json.loads(json.dumps(final_process_states))

    alternative_children = list(node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.prev_coll_bp =~ '{}'".format(app.app_name, curr_coll_bp['coll_bp_id'])))
    num_alternative_children = len(list(node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.prev_coll_bp =~ '{}'".format(app.app_name, curr_coll_bp['coll_bp_id']))))

    num_not_finished = 0

    for proc_name in alternative_processes:
        i = 0
        while (i < len(alternative_processes[proc_name])):
            if (alternative_processes[proc_name][i] != final_state_processes[proc_name][i]):
                num_not_finished += 1          
            i += 1

    children_exh = True
    for act_node in alternative_children:
        if (act_node['exhausted'] == "No"):
            children_exh = False
            break

    if ((num_not_finished == num_alternative_children) and (children_exh == True)):

        curr_coll_bp['exhausted'] = "Yes"
        neo_graph.push(curr_coll_bp)
        logger.info('Updated alternative coll. bp. "{}" to exhausted.'.format(curr_coll_bp['coll_bp_id']))

        if (curr_coll_bp['node_type'] != "root"):
            Update_closest_alternative_coll_bp(app, curr_coll_bp['coll_bp_id'], final_state_processes)
            return
        else:
            return

    logger.info('No (further) alternative parent node updated.')


def Is_app_root_exhausted(app_name):
    """Decides if the given application's root collective breakpoint is exhausted or not.

    Args:
        app_name (str): An application name.
    Returns:
        bool: True if root is exhausted, False if not.
    """

    conn_details = Read_connection_details(silent=True)
    neo_graph = conn_details[1]
    node_matcher = NodeMatcher(neo_graph)

    root_node = node_matcher.match('Collective_BP').where("_.app_name =~ '{}' AND _.node_type =~ '{}'".format(app_name, "root")).first()

    if (root_node == None):
        return False

    if (root_node['exhausted'] == "Yes"):
        return True
    else:
        return False

def Does_current_state_exist(app, app_instance, process_states):
    """Using the given application's current collective breakpoint, this function decides if the given state already exists or not.

    Args:
        app (Application): An Application instance.
        app_instance (Infrastructure): An Inrastructure instance.
        process_states (dict): A dictionary defining the state of each process in the instance.

    Returns:
        string: An empty string if the given state does not exist, otherwise the collective breakpoint's ID.
    """
    
    conn_details = Read_connection_details(silent=True)
    neo_graph = conn_details[1]
    node_matcher = NodeMatcher(neo_graph)

    child_nodes = list(node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.prev_coll_bp =~ '{}'".format(app.app_name, app_instance.curr_coll_bp)))
    node_id = ""

    if (len(child_nodes) >= 1):
        curr_proc_state = json.dumps(process_states)
        for act_node in child_nodes:
            node_proc_state = act_node['process_states']
            if (curr_proc_state == node_proc_state):
                node_id = act_node['coll_bp_id']
                break
    
    return node_id

def Get_list_of_children_nodes(app, coll_bp_id):
    """Gets a list of collective breakpoint IDs where their parent node is the given collective breakpoint.

    Args:
        app (Application): An Application.
        coll_bp_id (str): A collective breakpoint ID.

    Returns:
        list: A list of collective breakpoint IDs.
    """

    # Get Neo4j database connection details
    conn_details = Read_connection_details(silent=True)
    neo_graph = conn_details[1]
    node_matcher = NodeMatcher(neo_graph)

    children = list(node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.prev_coll_bp =~ '{}'".format(app.app_name, coll_bp_id)))

    children_nodes = []

    if (len(children) > 0):
        for act_node in children:
            children_nodes.append(act_node['coll_bp_id'])
    
    return children_nodes


def Does_coll_bp_exist(app, coll_bp_id):
    """Determines if the given collective breakpoint ID exists the given application's exection tree.

    Args:
        app (Application): An Application.
        coll_bp_id (string): A collective breakpoint ID.

    Returns:
        bool: True if the given collective breakpoint exists, False if not.
    """

    # Get Neo4j database connection details
    conn_details = Read_connection_details(silent=True)
    neo_graph = conn_details[1]

    node_matcher = NodeMatcher(neo_graph)

    coll_bp = node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.coll_bp_id =~ '{}'".format(app.app_name, coll_bp_id)).first()

    if (coll_bp == None):
        return False
    else:
        return True


def Get_process_states_of_coll_bp(app, coll_bp_id):
    """Gets the global state (process states) of the given collective breakpoint ID.

    Args:
        app (Application): An Application.
        coll_bp_id (string): A collective breakpoint ID.

    Returns:
        dict: A dict containing the process states for the given collective breakpoint. Otherwise an empty string.
    """
    
    if (Does_coll_bp_exist(app, coll_bp_id) == True):
        conn_details = Read_connection_details(silent=True)
        neo_graph = conn_details[1]

        node_matcher = NodeMatcher(neo_graph)

        return (node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.coll_bp_id =~ '{}'".format(app.app_name, coll_bp_id)).first()['process_states'])
    else:
        return ""


def Get_root_id_for_application(app):
    """Returns the root collective breakpoints ID for the given application.

    Args:
        app (Apllication): An Application isntance.

    Returns:
        string: The root ID ot an empty string ("") if it does not exist.
    """

    # Get Neo4j database connection details
    conn_details = Read_connection_details(silent=True)
    neo_graph = conn_details[1]

    node_matcher = NodeMatcher(neo_graph)

    root_node = node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.node_type =~ '{}'".format(app.app_name, "root")).first()

    # Root exists
    if (root_node != None):
        return root_node['coll_bp_id']
    else:
        return ""


def Get_next_coll_bp_id_to_target(app, start_coll_bp_id, target_coll_bp_id):
    """Gets the next collective breakpoint ID that leads to the given targeted collective breakpoint from the current collective breakpoint.

    Args:
        app (Application): An application
        start_coll_bp_id (string): Start collective breakpoint ID.
        target_coll_bp_id (string): Targeted collective breakpoint ID.

    Returns:
        string: A collective breakpoint ID if target can be reached from current breakpoint. Otherwise an empty string ("").
    """

    if (start_coll_bp_id == target_coll_bp_id):
        return ""
    elif (target_coll_bp_id == app.root_coll_bp):
        return app.root_coll_bp
    else:
        # Get Neo4j database connection details
        conn_details = Read_connection_details(silent=True)
        neo_graph = conn_details[1]

        node_matcher = NodeMatcher(neo_graph)

        path = []

        # Store target
        curr_node = node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.coll_bp_id =~ '{}'".format(app.app_name, target_coll_bp_id)).first()

        path.append(curr_node['coll_bp_id'])
        curr_node = node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.coll_bp_id =~ '{}'".format(app.app_name, curr_node['prev_coll_bp'])).first()

        # Move backwards until root or desired next state is reached
        while (curr_node['node_type'] != "root" and curr_node['coll_bp_id'] != start_coll_bp_id):
            path.append(curr_node['coll_bp_id'])
            curr_node = node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.coll_bp_id =~ '{}'".format(app.app_name, curr_node['prev_coll_bp'])).first()

        if (len(path) > 0):
            return path[-1]
        else:
            return ""