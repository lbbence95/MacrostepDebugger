# Module to handle Neo4j transactions, execution-tree operations

import data.repository as mstep_repo
from py2neo import Graph, Node, Relationship, NodeMatcher
import uuid, json, logging, os.path, re, yaml

import traceback

#Logger setup
logger = logging.getLogger('exectree')
logger.propagate = False
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
formatter = logging.Formatter('*** (%(asctime)s): %(message)s', "%Y-%m-%d %H:%M:%S")
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)


def Read_connection_details(app, silent=False):
    """Reads connection details from 'controller/neo4j_conn.yaml'.

    Args:
        app (Application): An Application instance.
        silent (bool, optional): Suppress console messages if conenction is OK. Defaults to False.

    Returns:
        tuple: A True boolean and a py2neo Graph object if connection can be established. Otherwise a False boolean and None.
    """

    neo_graph = None
    conn_details = {}

    try:
        # TO-DO: Use an Application instance to get connection details

        #neo4j_cfg = yaml.safe_load(open(os.path.join('controller','neo4j_conn.yaml')))

        #conn_details['host'] = neo4j_cfg['host'] 
        #conn_details['user'] = neo4j_cfg['user']
        #conn_details['password'] = neo4j_cfg['password']

        #TO-DO: use abstract graph-database authentication data
        conn_details['host'] = app.host
        conn_details['user'] = app.user
        conn_details['password'] = app.password

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

    conn_details = Read_connection_details(app, silent=True)
    neo_graph = conn_details[1]
 
    root_id = str(uuid.uuid4())

    # Create root node
    transact = neo_graph.begin()

    root_node = Node("Collective_BP", app_name=app.app_name, instance_ids=json.dumps([]), node_type="root", prev_coll_bp="", exhausted="No", coll_bp_id=root_id, process_states=json.dumps(process_states), collected_data=json.dumps([]), evaluation=json.dumps([]))

    transact.create(root_node)

    # Commit
    transact.commit()

    return root_id


def Create_collective_breakpoint(app, app_instance, process_states, satisfies_specification=False):
    """Inserts a new collective breakpoint into the application's execution tree.

    Args:
        app (Application): An Application.
        app_instance (Infrastructure): An application instance (Infrastructure).
        process_states (dict): A dictionary defining the state of each process in the instance.

    Returns:
        str: The newly created collective breakpoint's ID.
    """

    conn_details = Read_connection_details(app, silent=True)
    neo_graph = conn_details[1]
    node_matcher = NodeMatcher(neo_graph)

    # Create new node
    transact = neo_graph.begin()
    new_node = None
    coll_bp_id = str(uuid.uuid4())

    not_finished = mstep_repo.How_many_processes_havent_finished(app_instance.infra_id)

    if (not_finished == 0):
        # This is a final state
        new_node = Node("Collective_BP", app_name=app.app_name, instance_ids=json.dumps([]), node_type="final", prev_coll_bp=app_instance.curr_coll_bp, exhausted="Yes", coll_bp_id=coll_bp_id, process_states=json.dumps(process_states), collected_data=json.dumps([]), evaluation=json.dumps([]))
    elif (not_finished >= 2):
        # This is an alternative state
        new_node = Node("Collective_BP", app_name=app.app_name, instance_ids=json.dumps([]), node_type="alternative", prev_coll_bp=app_instance.curr_coll_bp, exhausted="No", coll_bp_id=coll_bp_id, process_states=json.dumps(process_states), collected_data=json.dumps([]), evaluation=json.dumps([]))
    elif (not_finished == 1):
        # This is a deterministic state
        new_node = Node("Collective_BP", app_name=app.app_name, instance_ids=json.dumps([]), node_type="deterministic", prev_coll_bp=app_instance.curr_coll_bp, exhausted="No", coll_bp_id=coll_bp_id, process_states=json.dumps(process_states), collected_data=json.dumps([]), evaluation=json.dumps([]))

    transact.create(new_node)

    # Create relationship between states
    prev_node = node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.coll_bp_id =~ '{}'".format(app.app_name, app_instance.curr_coll_bp)).first()  
    
    # Determine which process was stepped
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

    coll_bp_rel = Relationship(prev_node, "MACROSTEP", new_node, app_name=app.app_name, process_stepped="{}[{}]".format(process_stepped, i + 1))
    transact.create(coll_bp_rel)

    # Commit
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
    conn_details = Read_connection_details(app, silent=True)
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

        # If root is reached, no need to go backwards on path
        if (curr_coll_bp['node_type'] == "root"):
            # If root is exhausted return empty string, signaling
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
    conn_details = Read_connection_details(app, silent=True)
    neo_graph = conn_details[1]
    node_matcher = NodeMatcher(neo_graph)

    # Get previous collective breakpoint
    curr_coll_bp = node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.coll_bp_id =~ '{}'".format(app.app_name, curr_bp_id)).first()
    curr_coll_bp = node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.coll_bp_id =~ '{}'".format(app.app_name, curr_coll_bp['prev_coll_bp'])).first()

    is_root_or_alt = False
    if (curr_coll_bp['node_type'] == "root" or curr_coll_bp['node_type'] == "alternative"):
        is_root_or_alt = True
    else:
        # Set node exhausted flag and then push
        curr_coll_bp['exhausted'] = "Yes"
        neo_graph.push(curr_coll_bp)

    # Go backwards in tree until an alternative coll. bp. is found
    while (is_root_or_alt == False):
        curr_coll_bp = node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.coll_bp_id =~ '{}'".format(app.app_name, curr_coll_bp['prev_coll_bp'])).first()
        if (curr_coll_bp['node_type'] == "root" or curr_coll_bp['node_type'] == "alternative"):
            is_root_or_alt = True
        else:
            # Set node exhausted flag and then push
            curr_coll_bp['exhausted'] = "Yes"
            neo_graph.push(curr_coll_bp)
        
    # Get alternative coll. bp. process states and final process states to which later compare against
    alternative_processes = json.loads(curr_coll_bp['process_states'])
    final_state_processes = json.loads(json.dumps(final_process_states))

    # Get number of children nodes, aka. number of already traversed execution paths from the alternative breakpoint
    alternative_children = list(node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.prev_coll_bp =~ '{}'".format(app.app_name, curr_coll_bp['coll_bp_id'])))
    num_alternative_children = len(list(node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.prev_coll_bp =~ '{}'".format(app.app_name, curr_coll_bp['coll_bp_id']))))

    #Get number of non-finished processes at alternative coll. bp.
    num_not_finished = 0

    for proc_name in alternative_processes:
        i = 0
        while (i < len(alternative_processes[proc_name])):
            if (alternative_processes[proc_name][i] != final_state_processes[proc_name][i]):
                num_not_finished += 1          
            i += 1

    # Check if every child node is exhausted as well
    children_exh = True
    for act_node in alternative_children:
        if (act_node['exhausted'] == "No"):
            children_exh = False
            break

    # Check if exhausted, if so, then update
    if ((num_not_finished == num_alternative_children) and (children_exh == True)):

        # Set node exhausted flag and then push
        curr_coll_bp['exhausted'] = "Yes"
        neo_graph.push(curr_coll_bp)
        logger.info('Updated alternative coll. bp. "{}" to exhausted.'.format(curr_coll_bp['coll_bp_id']))

        # If coll. bp. is root, then no need to continue updating parent nodes, since no parent node exists
        if (curr_coll_bp['node_type'] != "root"):
            Update_closest_alternative_coll_bp(app, curr_coll_bp['coll_bp_id'], final_state_processes)
            return
        else:
            return

    logger.info('No (further) alternative parent node updated.')

def Update_node_app_specification_evaluation(app, new_data, app_instance_id, coll_bp_id):
    """Adds the evaluated specification to the node.

    Args:
        app (Application): An Application.
        new_data (dict): A dictionary of the new instance's collected data at the node.
        app_instance_id (string): An application instance ID to store.
        coll_bp_id (string): A collective breakpoint ID identifing a collective breakpoint in the application's exectuion tree.
    """

    conn_details = Read_connection_details(app, silent=True)
    neo_graph = conn_details[1]
    node_matcher = NodeMatcher(neo_graph)

    coll_bp_to_update = node_matcher.match('Collective_BP').where("_.app_name =~ '{}' AND _.coll_bp_id =~ '{}'".format(app.app_name, coll_bp_id)).first()

    specification = ""

    operators_shorthand = {'equals': '=', 'not_equals':'<>', 'less_than_eq':'<=', 'less_than':'<', 'greater_than_eq':'>=', 'greater_than':'>', 'between': '><', 'exactly':'exactly', 'contains':'contains'}

    print('')
    try:
        specification = yaml.safe_load(open(app.app_desc_file, 'r'))['specification']

        processes_data = {}
        processes_evaluated = {}
        for act_proc_name in new_data[app_instance_id].keys():
            processes_data[act_proc_name] = {}
            processes_evaluated[act_proc_name] ={}

            for act_proc_num in new_data[app_instance_id][act_proc_name].keys():
                processes_data[act_proc_name][act_proc_num] = {}
                processes_evaluated[act_proc_name][act_proc_num] = {}

                for act_proc_var_group in new_data[app_instance_id][act_proc_name][act_proc_num].keys():
                    for act_proc_var, act_proc_var_value in new_data[app_instance_id][act_proc_name][act_proc_num][act_proc_var_group].items():
                        processes_data[act_proc_name][act_proc_num][act_proc_var] = act_proc_var_value
                        processes_evaluated[act_proc_name][act_proc_num][act_proc_var] = None


        for act_proc_name, variables_list in specification.items():
            
            num_of_act_proc_name = 0
            try:
                num_of_act_proc_name = len( processes_data[act_proc_name].items() )
            except KeyError:
                print(f'\tCould not evalute {variable_name} for processes {act_proc_name}.')
                continue

            for act_variable in variables_list:
                
                i = 0
                variable_name = act_variable["variable"]["name"]

                while (i < num_of_act_proc_name):
                    variable_operator = list(act_variable['variable']['expected'].keys())

                    if ( act_proc_name in processes_data.keys() and variable_name in processes_data[act_proc_name][i + 1].keys() and variable_operator[0] in operators_shorthand.keys() ):
                        received_data = processes_data[act_proc_name][i + 1][variable_name]
                        processes_evaluated[act_proc_name][i + 1][variable_name] = Evaluate_existing_process_variable(received_data, variable_operator[0], act_variable['variable']['expected'][variable_operator[0]])

                        if ( variable_operator[0] == "between" ):
                            print(f"\tCould evaluate '{variable_name}' for process {act_proc_name}[{i + 1}], expected '{received_data} {operators_shorthand[variable_operator[0]]} {act_variable['variable']['expected'][variable_operator[0]][:2]}', got: '{received_data}' ({processes_evaluated[act_proc_name][i + 1][variable_name]})")
                        else:
                            print(f"\tCould evaluate '{variable_name}' for process {act_proc_name}[{i + 1}], expected '{received_data} {operators_shorthand[variable_operator[0]]} {act_variable['variable']['expected'][variable_operator[0]]}', got: '{received_data}' ({processes_evaluated[act_proc_name][i + 1][variable_name]})")
                    else:
                        print(f'\tCould not evalute {variable_name} for process {act_proc_name}[{i + 1}]')

                    i += 1
             
    except Exception:
        tb = traceback.format_exc()
        print('An error has occured...\r\n{}\r\n'.format(tb))
        pass
    print('')

    processes_evaluated['_GLOBAL'] = None
    global_predicate = yaml.safe_load(open(app.app_desc_file, 'r'))['specification_global']
    global_predicate_evaluated = None
    if ( Check_process_and_variable_names(global_predicate, processes_evaluated) == True ):
        new_string = re.split(r'( and | or |\(|\))', global_predicate)
        new_string_2 = []
        for act_split in new_string:
            to_append = act_split
            if ' is ' in act_split:
                variable_string = re.split(r"( is )", act_split)
                variable_value = Get_variable_value(variable_string[0], processes_evaluated)
                variable_string[0] = "".join([str(variable_value), ' '])
                variable_string[1] = ' == '
                to_append = "".join(act_item for act_item in variable_string)
    
            new_string_2.append(to_append)
        
        global_predicate_evaluated = eval("".join(act_item for act_item in new_string_2))

        print(f'\tTo evalueate: \t{global_predicate}')
        print(f'\tSubstituted: \t{"".join(act_item for act_item in new_string_2)}')
        print(f'\tEvaluation: \t{global_predicate_evaluated}\r\n')

    processes_evaluated['_GLOBAL'] = global_predicate_evaluated
    new_evaluation = {}
    new_evaluation[app_instance_id] = processes_evaluated
    evaluated = list(json.loads(coll_bp_to_update['evaluation']))
    evaluated.append(new_evaluation)

    coll_bp_to_update['evaluation'] = json.dumps(evaluated)

    neo_graph.push(coll_bp_to_update)

def Get_variable_value(string, processes):
    #TO-DO: documentation

    splitted_string = re.split(r'(\.)', string)
    next_splitted_string = re.split(r'(\[.*\])', splitted_string[0])
    
    proc_name=next_splitted_string[0].strip()
    proc_num=int(next_splitted_string[1].replace('[','').replace(']',''))
    proc_num_var=splitted_string[2].strip()

    return processes[proc_name][proc_num][proc_num_var]


def Check_process_and_variable_names(string, processes):
    #TO-DO: documentation

    new_string = re.split(r'( and | or |\(|\))', string)

    for act_split in new_string:
        if ' is ' in act_split:
            variable_string = re.split(r"( is )", act_split)    
            splitted_string = re.split(r'(\.)', variable_string[0])
            next_splitted_string = re.split(r'(\[.*\])', splitted_string[0])

            proc_name=next_splitted_string[0].strip()
            proc_num=-1
            proc_num_var=splitted_string[2].strip()
            
            if proc_name not in processes.keys():
                print('Non-existing process name detected. Please check expression!')
                return False

            try:
                proc_num=int(next_splitted_string[1].replace('[','').replace(']',''))
            except ValueError:
                print('Invalid process number detected. Please check expression!')
                return False

            if proc_num not in processes[proc_name].keys():
                print('Non-existing process number detected. Please check expression!')
                return False
            
            if (proc_num_var not in processes[proc_name][proc_num].keys()):
                print('Non-existing process variable detected. Please check expression!')
                return False

    #print('All process names, numbers and variables were found!')
    return True

def Update_node(app, coll_bp_id, app_instance_id):
    """Adds the given application instance ID to the given collective breakpoint's instance IDs list. Also appends new collected data to the node, using the given instance ID.

    Args:
        app (Application): An Application.
        coll_bp_id (string): A collective breakpoint ID identifing a collective breakpoint in the application's exectuion tree.
        app_instance_id (string): An application instance ID to store.
    """

    conn_details = Read_connection_details(app, silent=True)
    neo_graph = conn_details[1]
    node_matcher = NodeMatcher(neo_graph)

    coll_bp_to_update = node_matcher.match('Collective_BP').where("_.app_name =~ '{}' AND _.coll_bp_id =~ '{}'".format(app.app_name, coll_bp_id)).first()

    app_instance_ids = list(json.loads(coll_bp_to_update['instance_ids']))
    app_instance_ids.append(app_instance_id)

    coll_bp_to_update['instance_ids'] = json.dumps(app_instance_ids)
    neo_graph.push(coll_bp_to_update)

    # Store data at coll. bp.
    new_data = {}
    new_data[app_instance_id] = mstep_repo.Get_app_instance_curr_coll_bp_data(app, app_instance_id)

    collected_data = list(json.loads(coll_bp_to_update['collected_data']))
    collected_data.append(new_data)

    coll_bp_to_update['collected_data'] = json.dumps(collected_data)

    neo_graph.push(coll_bp_to_update)

    # Check if state satisfies specification
    Update_node_app_specification_evaluation(app, new_data, app_instance_id, coll_bp_id)

def Is_app_root_exhausted(app):
    """Decides if the given application's root collective breakpoint is exhausted or not.

    Args:
        app (Application): An Application instance.
    Returns:
        bool: True if root is exhausted, False if not.
    """

    conn_details = Read_connection_details(app, silent=True)
    neo_graph = conn_details[1]
    node_matcher = NodeMatcher(neo_graph)

    root_node = node_matcher.match('Collective_BP').where("_.app_name =~ '{}' AND _.node_type =~ '{}'".format(app.app_name, "root")).first()

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
    
    conn_details = Read_connection_details(app, silent=True)
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
    conn_details = Read_connection_details(app, silent=True)
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
    conn_details = Read_connection_details(app, silent=True)
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

        # Get Neo4j database connection details
        conn_details = Read_connection_details(app, silent=True)
        neo_graph = conn_details[1]

        node_matcher = NodeMatcher(neo_graph)

        return (node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.coll_bp_id =~ '{}'".format(app.app_name, coll_bp_id)).first()['process_states'])
    else:
        return ""

def Get_root_id_for_application(app):
    """Returns the root collective breakpoints ID for the given application.

    Args:
        app (Apllication): An Application instance.

    Returns:
        string: The root ID ot an empty string ("") if it does not exist.
    """

    # Get Neo4j database connection details
    conn_details = Read_connection_details(app, silent=True)
    neo_graph = conn_details[1]

    node_matcher = NodeMatcher(neo_graph)

    root_node = None

    try:
        root_node = node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.node_type =~ '{}'".format(app.app_name, "root")).first()
    except AttributeError:
        # No root found
        pass

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
        conn_details = Read_connection_details(app, silent=True)
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

def Evaluate_existing_process_variable(received_data: str, operator: str, expected: str) -> bool:
    """Evaluates if the input received variable value satisfies the condition against the expected value.

    Args:
        received_data (str): Received variable data value.
        operator (str): A string indicating the operation.
        expected (str): Expected value.

    Returns:
        bool: True if the received variable data value equals to the expected value. Else false.
    """

    ret_value = False

    if (operator == 'equals' and received_data != ""):
        ret_value = eval('float(received_data) == float(expected)')
    elif (operator == 'not_equals'):
        if ( received_data != "" ):
            ret_value = eval('float(received_data) != float(expected)')
        else:
            ret_value = True
    elif (operator == 'less_than_eq' and received_data != ""):
        ret_value = eval('float(received_data) <= float(expected)')
    elif (operator == 'less_than' and received_data != ""):
        ret_value = eval('float(received_data) < float(expected)')
    elif (operator == 'greater_than_eq' and received_data != ""):
        ret_value = eval('float(received_data) >= float(expected)')
    elif (operator == 'greater_than' and received_data != ""):
        ret_value = eval('float(received_data) > float(expected)')
    elif (operator == 'between' and received_data != ""):
        expected = expected[:2]
        ret_value = eval('float(min(expected)) < float(received_data) < float(max(expected))')
    elif (operator == 'exactly'):
        ret_value = (str(received_data) == str(expected))
    elif (operator == 'contains' and received_data != ""): 
        ret_value = (str(expected) in received_data)
    else:
        ret_value = False
        
    return ret_value