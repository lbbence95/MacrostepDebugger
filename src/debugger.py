# Represents the main file of the debugger with CLI functions

import src.api.rest as msteprest
import src.util.consolelogs as mstep_conlogger

import argparse


parser = argparse.ArgumentParser(description='Macrostep based debugger')
group_basic = parser.add_mutually_exclusive_group()

# Listing
group_basic.add_argument('-li','--infrastructures', action='store_true', help='list managed infrastructures')
group_basic.add_argument('-ln','--nodes', action='store_true', help='list managed nodes')

# Service start
group_basic.add_argument('-s','--start', action='store_true', help='start the macrostep debugger service (can be used with -p)')
parser.add_argument('-p', '--port', type=str, metavar='', help='macrostep debugger service port (default is 5000)')

# Details
parser.add_argument('-dn','--detailsnode', type=str, metavar='', help='show details of the given node (Important! Used after option -di, cannot be used on its own)')
parser.add_argument('-di','--detailsinfra', type=str, metavar='', help='show details of the given infrastructure.')

# Update
parser.add_argument('-i', '--infra', type=str, metavar='', help='permit a node in the given infrastructure to move to the next breakpoint')
parser.add_argument('-n','--node', type=str, metavar='', help='a node ID (Important! Used after option -i, cannot be used on its own)')

args = parser.parse_args()


if __name__ == "__main__":
    """Sets Flask configuration.
    """

    # -li: List infrastructures
    if args.infrastructures == True:
        msteprest.mstep_conlogger.PrintManagedInfras()

    # -ln: List nodes
    elif args.nodes == True:
        msteprest.mstep_conlogger.PrintManagedNodes()
    
    # -di:
    elif args.detailsinfra != None:

        if args.detailsnode != None:
            mstep_conlogger.PrintNode(args.detailsinfra, args.detailsnode)
        else:
            mstep_conlogger.PrintInfra(args.detailsinfra)
    
    # -i and -n
    elif args.infra != None and args.node != None:

        if msteprest.mstepcontroller.NodeExists(args.infra, args.node) == True:
            # TO-DO: Refactoring, mstepcontroller...
            msteprest.mstepcontroller.MoveNodeToNext(args.infra, args.node)
            # TEST
            mstep_conlogger.PrintNode(args.infra, args.node)
        else:
            mstep_conlogger.PrintInfra(args.infra)
    

    # -s: Start the service
    if args.start == True:
        msteprest.Init()

        if args.port != None:
            try:
                if int(args.port) and int(args.port) > 0 and int(args.port) <= 65535:
                    msteprest.app.run(host = '0.0.0.0', port=int(args.port), debug = True, threaded=True)
                else:
                    print('Invalid port!')
            except ValueError:
                print('Invalid port!')

        else:
            msteprest.app.run(host = '0.0.0.0', port=5000, debug = True, threaded=True)