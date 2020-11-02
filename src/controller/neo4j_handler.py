# Module to handle Neo4j transactions.

from data import repository as msteprepo
from py2neo import Database, Graph, Node, Relationship, NodeMatcher, NodeMatch
from time import strftime
import datetime, uuid, json

def SendData(infra_list):
    """Send the details of the given infrastructure(s) to the configured Neo4j database.

    Args:
        infra_list (list): A string list.

    Returns:
        bool: True if successful transactions. Otherwise False.
    """

    # Get a valid infrastructure list
    infras = GetValidInfrastructures(infra_list)
    
    # Check if there is atleast one valid infrastructure.
    if len(infras) == 0:
        print('\r\n*** No valid infrastructures given or no infrastructures managed!')
        return False
    elif len(infras) > 0:

        conn_details = ReadConnectionDetails()
        neo_graph = None

        if conn_details[0] == True:
            neo_graph = conn_details[1]
        else:
            return False

        # Iterate over infrastructures
        for infra_id in infras:

            act_infra = msteprepo.ReadInfrastructure(infra_id)[0]
            g_node_infra = Node("Infrastructure", infra_id=act_infra[0], infra_name=act_infra[1], infra_reg=act_infra[2])

            transact = neo_graph.begin()           
            transact.create(g_node_infra)

            nodes = msteprepo.ReadNodesFromInfra(act_infra[0])

            # Iterate over nodes
            for act_node in nodes:
                g_node_node = Node("Node", infra_id=act_node[0], node_id=act_node[1], node_name=act_node[2], pub_ip=act_node[6], curr_bp=act_node[4], node_reg=act_node[3])
                infra_node_rel = Relationship(g_node_infra, "CONTAINS", g_node_node, since=act_node[3])

                transact.create(g_node_node)
                transact.create(infra_node_rel)

                bps = msteprepo.ReadBreakpoint(act_node[0], act_node[1])

                act_bp_id = 0
                g_node_prev_bp = None
                time_reached_prev_bp = None

                # Iterate over breakpoints
                while act_bp_id < len(bps):
                    
                    # Check for first breakpoint
                    if act_bp_id == 0:
                        g_node_bp = Node("Breakpoint", tags=bps[act_bp_id][5], bp_id=bps[act_bp_id][3], bp_reg=bps[act_bp_id][2])
                        node_bp_rel = Relationship(g_node_node, "REACHED", g_node_bp, reached_at=bps[act_bp_id][2])

                        transact.create(g_node_bp)
                        transact.create(node_bp_rel)
                        
                        time_reached_prev_bp = bps[act_bp_id][2]
                        g_node_prev_bp = g_node_bp
                        act_bp_id += 1
                    else:
                        # Calculate delta time between breakpoints
                        bp_delta_time = str(datetime.datetime.strptime(bps[act_bp_id][2], '%Y.%m.%d. %H:%M:%S.%f') - datetime.datetime.strptime(time_reached_prev_bp, '%Y.%m.%d. %H:%M:%S.%f'))[:-3]

                        g_node_bp = Node("Breakpoint", tags=bps[act_bp_id][5], bp_id=bps[act_bp_id][3], bp_reg=bps[act_bp_id][2])
                        node_bp_rel = Relationship(g_node_node, "REACHED", g_node_bp, reached_at=bps[act_bp_id][2])

                        transact.create(g_node_bp)
                        transact.create(node_bp_rel)

                        # Include delta time between breakpoints
                        bp_bp_rel = Relationship(g_node_prev_bp, "NEXT", g_node_bp, next_at=bps[act_bp_id][2], delta_time=bp_delta_time)

                        transact.create(bp_bp_rel)

                        time_reached_prev_bp = bps[act_bp_id][2]
                        g_node_prev_bp = g_node_bp
                        act_bp_id += 1

            transact.commit()
            print('*** ({}) Transaction sent! (Infrastructure: {})'.format(datetime.datetime.now().strftime('%Y.%m.%d. %H:%M:%S.%f')[:-3], act_infra[0]))

        return True
    else:
        print('*** No valid infrastructures given or no infrastructures managed!')
        return False

def ReadConnectionDetails():
    """Reads connection details from the "neo4j_conn.cfg" file.

    Returns:
        tuple: A True boolean and a py2neo Graph object if connection can be established. Otherwise False and None.
    """

    neo_graph = None
    conn_details = {}

    # Check config file
    try:
        with open('src/neo4j_conn.cfg') as f_cfg:
            for line in f_cfg:
                line = line[:-1]
                (key, val) = line.split('=')
                conn_details[str(key)] = val
    
        neo_graph = Graph(conn_details['host'], user=conn_details['user'], password=conn_details['password'], secure=False)
    except FileNotFoundError:
        print('\r\n*** Configuration file does not exist, please create one!')
        return (False, neo_graph)
    except ValueError:
        print('\r\n*** Invalid configuration file!')
        return (False, neo_graph)
    except KeyError:
        print('\r\n*** Invalid configuration file!')
        return (False, neo_graph)

    # Testing connection
    print('\r\n*** Connecting to database...')
    try:
        neo_graph.run("Match () Return 1 Limit 1")
        print('*** Connection ok!')
        return (True, neo_graph)
    except Exception:
        print('*** Connection error!')
        return (False, neo_graph)

def RootInfraAppPair(infra_id, app_name):
    """Processes an infrastructure-application pair. The infrastructure has to be in a root state.

    Args:
        infra_id (string): An infrastructure ID.
        app_name (string): An application name.

    Returns:
        tuple: A bool and a string. If the process succeded, the bool is True. Otherwise False. String is a description message.
    """

    # Check if pairing already exists
    app_infra_pairs = msteprepo.ReadTrackTable()
    for act_pair in app_infra_pairs:
        if (act_pair[0] == app_name) or (act_pair[1] == infra_id):
            return (False, 'Application name already exists, or infrastructure already paired.')

    # Check root state
    if CheckIfRootState(infra_id) == True:

        # Check Neo4j connection
        conn_details = ReadConnectionDetails()
        if (conn_details[0] == False):
            return (False, 'Connection error. Please check Neo4j configuration file.')

        # Get root node
        neo_graph = conn_details[1]
        node_matcher = NodeMatcher(neo_graph)
        root_node = node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.node_type =~ '{}'".format(app_name, "root")).first()

        # Check if there is a root. None means it does not exist
        if root_node != None:
            msteprepo.RegisterTrackEntry(app_name, infra_id, root_node['coll_bp_id'])
            return (True, 'Root node already exists. No root created. Tracking infrastructure "{}".'.format(infra_id))
        else:
            print('*** Root does not exist. Creating root collective breakpoint.')

            # Gather infrastructure state data
            root_node_bp_id = str(uuid.uuid4())
            process_states = GetNodeStates(infra_id)
            prev_coll_bp_ID = "none"

            # Create root node
            transact = neo_graph.begin()
            root_node = Node("Collective_BP", app_name=app_name, infra_id=infra_id, node_type="root", prev_coll_bp=prev_coll_bp_ID, coll_bp_id=root_node_bp_id, process_states=json.dumps(process_states))
            transact.create(root_node)
            transact.commit()

            # Store the infra-app pair as tracked
            msteprepo.RegisterTrackEntry(app_name, infra_id, root_node_bp_id)

            print('*** ({}) Transaction sent! (Application name: "{}", infrastructure: "{}" paired)'.format(datetime.datetime.now().strftime('%Y.%m.%d. %H:%M:%S.%f')[:-3], app_name, infra_id))
            return ( True, 'Infrastructure "{}" was in root state. Root node and pairing created.'.format(infra_id) )

    else:
        return ( False, 'Current state is not a valid root state. Make sure every node is at its first breakpoint, and no node is permitted.' )

def SendCollectiveBreakpoint(infra_id):
    # Check if global state is consistent and not a root (every node is waiting)
    if (CheckGlobalState(infra_id) and not CheckIfRootState(infra_id)) == True:

        # Check Neo4j connection
        conn_details = ReadConnectionDetails()
        if (conn_details[0] == False):
            return (False, 'Connection error. Please check Neo4j configuration file.')
        
        # Get previous node
        tracked_pair = msteprepo.ReadSingleTrackEntry(infra_id)[0]
        neo_graph = conn_details[1]
        node_matcher = NodeMatcher(neo_graph)

        prev_node = node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.coll_bp_id =~ '{}'".format(tracked_pair[0], tracked_pair[2])).first()

        # Check for none
        if (prev_node != None):

            # Gather data
            coll_bp_id = str(uuid.uuid4())
            process_states = GetNodeStates(infra_id)
            prev_coll_bp = tracked_pair[2]
            
            # Check for existing child node
            child_nodes = list(node_matcher.match("Collective_BP").where("_.app_name =~ '{}' AND _.prev_coll_bp =~ '{}'".format(tracked_pair[0], tracked_pair[2])))

            if (len(child_nodes) == 0):
                # No children, create new collective breakpoint
                transact = neo_graph.begin()

                new_node = Node("Collective_BP", app_name=tracked_pair[0], infra_id=infra_id, node_type="other", prev_coll_bp=prev_coll_bp, coll_bp_id=coll_bp_id, process_states=json.dumps(process_states))
                transact.create(new_node)

                coll_bp_rel = Relationship(prev_node, "MACROSTEP", new_node, app_name=tracked_pair[0], infra_id=infra_id)
                transact.create(coll_bp_rel)
                transact.commit()

                # Update current breakpoint field
                msteprepo.UpdateTrackTableEntryPrevBP(infra_id, coll_bp_id)

                return (True, 'Success, new collective breakpoint created.')
            #if (len(child_nodes) > 0):
            else:
                # There are children nodes, check for equal process state
                for act_node in child_nodes:
                    # Get node state
                    act_state = json.loads(act_node["process_states"])

                    if act_state == process_states:
                        # Equal process state, store BP node
                        print('*** Existing global state detected!')
                        msteprepo.UpdateTrackTableEntryPrevBP(infra_id, act_node["coll_bp_id"])
                        return (True, 'Success. No new BP needed.')
                
                # Create new collective breakpoint
                transact = neo_graph.begin()
                new_node = Node("Collective_BP", app_name=tracked_pair[0], infra_id=infra_id, node_type="other", prev_coll_bp=prev_coll_bp, coll_bp_id=coll_bp_id, process_states=json.dumps(process_states))
                transact.create(new_node)

                # Create relationship
                coll_bp_rel = Relationship(prev_node, "MACROSTEP", new_node, app_name=tracked_pair[0], infra_id=infra_id)
                transact.create(coll_bp_rel)
                transact.commit()

                # Update previous breakpoint filed in the tracking table
                msteprepo.UpdateTrackTableEntryPrevBP(infra_id, coll_bp_id)

                return (True, 'Success, new collective breakpoint created.')  
        else:
            return (False, 'Unexpected error. Node not found.')
    else:
        return (False, 'Infrastructure "{}" is not in a consistent global state.'.format(infra_id))
        
def StopTracking(infra_id):
    msteprepo.RemoveInfraApp(infra_id)

def IsInfraTracked(infra_id):
    
    tracked = False
    app_infra_pair = msteprepo.ReadTrackTable()

    # Check if given infra is already tracked
    for act_pair in app_infra_pair:
        if (act_pair[1] == infra_id):
            tracked = True
            break
    
    return tracked

def CheckIfRootState(infra_id):
    """Checks if the given ifrastructure is in a root state. Meaning every node is at its first breakpoint and they are not permitted to move to the next breakpoint.

    Args:
        infra_id (string): An infrastructure ID.

    Returns:
        boolean: True if the infrastructure is in a root state. False if not.
    """

    root_state = True
    nodes = msteprepo.ReadNodesFromInfra(infra_id)

    for act_node in nodes:
        if act_node[4] != 1 or act_node[5] != 0:
            root_state = False
            break
    
    return root_state

def CheckGlobalState(infra_id):

    global_state = True
    nodes = msteprepo.ReadNodesFromInfra(infra_id)

    for act_node in nodes:
        if act_node[5] != 0:
            global_state = False
            break
    
    return global_state

def GetNodeStates(infra_id):
    """Returns a dictionary containing the node's name and its current breakpoint.

    Args:
        infra_id (string): An infrastructure ID.

    Returns:
        dict: A dictionary containing a node name and a breakpoint number.
    """

    node_states = {}
    nodes = msteprepo.ReadNodesFromInfra(infra_id)

    for act_node in nodes:
        node_states[str(act_node[2])] = str(act_node[4])
    
    return dict(sorted(node_states.items(), key=lambda x: x[0], reverse=False))

def GetValidInfrastructures(list_infras):
    """Returns a list of valid (existing) infrastructures from the given list of infrastructures.

    Args:
        list_infras (list): A string list containing a list of infrastructure IDs.

    Returns:
        list: A string list containing valid infrastructure IDs without duplicates.
    """

    valid_list = []

    # Collect existing infrastructures
    for act_infra in list_infras:
        if len(msteprepo.ReadInfrastructure(act_infra)) != 0:
            valid_list.append(act_infra)
    
    # Remove duplicates
    if len(valid_list) != len(set(valid_list)):
        valid_list = list(set(valid_list))
    
    return valid_list