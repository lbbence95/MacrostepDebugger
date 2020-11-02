#!/usr/bin/env python3

# Represents the main file of the debugger with CLI functions

from util import consolelogs as mstep_conlogger
from api import rest as msteprest
from controller import controller as mstepcontroller
from controller import neo4j_handler as mstepneo4j_handler
import argparse

parser = argparse.ArgumentParser(description='Macrostep based cloud-orchestration debugger (Prototype, 2020)')
exclusive_group = parser.add_mutually_exclusive_group()
exclusive_sub_group = parser.add_mutually_exclusive_group()

### Main options
# Listing
exclusive_group.add_argument('-li','--list_infrastructures', action='store_true', help='list managed infrastructures')
exclusive_group.add_argument('-ln','--list_nodes', action='store_true', help='list managed nodes')

# Service start
exclusive_group.add_argument('-s','--start', action='store_true', help='start the macrostep debugger service (default port: 5000)')

# Details
exclusive_group.add_argument('-di','--details_infra', type=str, metavar='Infra_ID', help='show details of a given infrastructure.')

# Update
exclusive_group.add_argument('-i', '--infrastructure', type=str, metavar='Infra_ID', help='permit all nodes in the given infrastructure to move to the next breakpoint')

# Neo4j
exclusive_group.add_argument('-n4','--neo4j', type=str, metavar='Infra_ID', nargs='+', default=[], help='send infrastructure details to a predetermined Neo4j database')

# Clear database
exclusive_group.add_argument('-c','--clear', action='store_true', help="clear the debugger's internal database")

# Macrostep
exclusive_group.add_argument('-t', '--track_infra', type=str, metavar='Infra_ID', nargs=1, help='a(n ochestrator) given infrastrucutre ID to track (can only be used with option "-ap")')
exclusive_group.add_argument('-st', '--stop_tracking', type=str, metavar='Infra_ID', nargs=1, help='stop tracking the given infrastructure')

### Sub-options
# Service start
exclusive_sub_group.add_argument('-p', '--port', type=str, metavar='Portnumber', help='macrostep debugger service port (can only be used with option "-s")')

# Details
exclusive_sub_group.add_argument('-dn','--details_node', type=str, metavar='Node_ID', help='show details of a given node (can only be used with option "-di")')

# Update
exclusive_sub_group.add_argument('-n','--node', type=str, metavar='Node_ID', nargs='+', help='permit only the given nodes in the infrastructure to move to the next breakpoint (can only be used with option "-i")')

# Macrostep
exclusive_sub_group.add_argument('-ap', '--application', type=str, metavar='Application_name', nargs=1, help='an application/infrastructure name on which the macrostep process is executed (can only be used with option "-t")')

args = parser.parse_args()

if __name__ == "__main__":
    # -li: List infrastructures
    if args.list_infrastructures == True:
        mstep_conlogger.PrintManagedInfras()

    # -ln: List nodes
    elif args.list_nodes == True:
        mstep_conlogger.PrintManagedNodes()
    
    # -di and -dn: Infrastructure details
    elif args.details_infra != None:
        if args.details_node != None:
            mstep_conlogger.PrintNode(args.details_infra, args.details_node)
        else:
            mstep_conlogger.PrintInfra(args.details_infra)
    elif args.details_node != None:
        print('\r\n*** Use "-dn" with option "-di"!')
    
    # -i and -n: Permit next breakpoint
    elif args.infrastructure != None:
        if mstepcontroller.InfraExists(args.infrastructure) == True:
            if args.node != None:
                moved_node = False
                # Both -i and -n
                for act_node in args.node:
                    if mstepcontroller.NodeExists(args.infrastructure, act_node) == True:
                        mstepcontroller.MoveNodeToNext(args.infrastructure, act_node)
                        moved_node = True
                    else:
                        print('\r\n*** No node with ID "{}" exists in infrastructure with ID "{}"!'.format(act_node, args.infrastructure))
                
                if moved_node == True:
                    mstep_conlogger.PrintInfra(args.infrastructure)
            else:
                # Only -i
                mstepcontroller.MoveAllNodesInInfraToNext(args.infrastructure)
                mstep_conlogger.PrintInfra(args.infrastructure)
            
        else:
           print('\r\n*** No infrastructure exists with ID "{}"!'.format(args.infrastructure))

    # -n: Node option alone
    elif args.node != None:
        print('\r\n*** Use "-n" with option "-i"!')
    
    # -n4: Noe4j connection
    elif len(args.neo4j) != 0:
        mstepneo4j_handler.SendData(args.neo4j)
    
    # -c: Clear database
    elif args.clear == True:
        mstepcontroller.ClearDatabase()
        mstep_conlogger.DatabaseRecordsDroppedMessage()
    
    # -t: Track infrastructure
    elif args.track_infra != None:
        if mstepcontroller.InfraExists(args.track_infra[0]):
            if args.application != None:
                result = mstepneo4j_handler.RootInfraAppPair(args.track_infra[0], args.application[0])
                print('\r\n*** {}'.format(result[1]))
            else:
                print('\r\n*** Use "-t" with option "-ap"!')
        else:
            print('\r\n*** No infrastructure exists with ID "{}"!'.format(args.track_infra[0]))

    # -st: Stop tracking
    elif args.stop_tracking != None:
        if mstepcontroller.InfraExists(args.stop_tracking[0]):
            mstepneo4j_handler.StopTracking(args.stop_tracking[0])
            print('\r\n*** Stopped tracking infrastructure "{}".'.format(args.stop_tracking[0]))
        else:
            print('\r\n*** No infrastructure-application pair exists with infrastructure ID "{}"!'.format(args.stop_tracking[0]))

    # -ap: Application option alone
    elif args.application != None:
        print('\r\n*** Use "-ap" with option "-t"!')

    # -s: Start service
    elif args.start == True:
        mstepcontroller.Initialize()

        if args.port != None:
            try:
                if int(args.port) and int(args.port) > 0 and int(args.port) <= 65535:
                    msteprest.app.run(host = '0.0.0.0', port=int(args.port), debug = True, threaded=True)
                else:
                    print('\r\n*** Invalid port!')
            except ValueError:
                print('\r\n*** Invalid port!')
        else:
            msteprest.app.run(host = '0.0.0.0', port=5000, debug = True, threaded=True)
    
    # -p: Port alone
    elif args.start != None:
        print('\r\n*** Use "-p" with option "-s"!')