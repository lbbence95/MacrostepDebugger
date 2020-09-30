# Module to handle Neo4j transactions.

from data import repository as msteprepo
from py2neo import Database, Graph, Node, Relationship
from time import strftime

import datetime

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

        # Read connection details
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
            return False
        except ValueError:
            print('\r\n*** Invalid configuration file!')
            return False
        except KeyError:
            print('\r\n*** Invalid configuration file!')
            return False     

        # Testing connection
        print('\r\n*** Connecting to database...')
        try:
            neo_graph.run("Match () Return 1 Limit 1")
            print('*** Connection ok!')
        except Exception:
            print('*** Connection error!')
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