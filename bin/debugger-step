#!/usr/bin/env python

#CLI functions related to controlling infrastructure deployment

from controller import controller as mstep_controller
from util import logger as mstep_logger
import argparse, logging

#Logger setup
logger = logging.getLogger('debugger_step')
logger.propagate = False
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
formatter = logging.Formatter('*** (%(asctime)s): %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

#Options and suboptions
parser = argparse.ArgumentParser(description='Commands and options related to controlling infrastructure deployment.')
exclusive_group = parser.add_mutually_exclusive_group()
exclusive_sub_group = parser.add_argument_group()

#Option: define infrastructure
exclusive_group.add_argument('-i', '--infrastructure', type=str, metavar='INFRA_ID', help='permit all nodes in the given infrastructure to move to the next breakpoint')
#Suboption: define nodes
exclusive_sub_group.add_argument('-n','--node', type=str, metavar='NODE_ID', nargs='+', help='permit only the given nodes in the given infrastructure to move to the next breakpoint')

#Argparse
args = parser.parse_args()

if __name__ == "__main__":
    # -i and -n: Permit next breakpoint
    if args.infrastructure != None and args.node == None:
        #Step whole infrastructure
        mstep_controller.Step_whole_infra(args.infrastructure)
        mstep_logger.Print_infra(args.infrastructure)
    elif args.infrastructure != None and args.node != None:
        #Step only the given nodes in the given infrastructure
        mstep_controller.Step_given_nodes(args.infrastructure, args.node)
        mstep_logger.Print_infra(args.infrastructure)
    elif args.node != None:
        print('*** Use "-n" with option "-i"!')