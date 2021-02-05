#!/usr/bin/env python

#CLI functions related to infrastructure and node details, list.

from util import logger as mstep_logger
import argparse, logging

#Logger setup
logger = logging.getLogger('debugger_list')
logger.propagate = False
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
formatter = logging.Formatter('*** (%(asctime)s): %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

#Options and suboptions
parser = argparse.ArgumentParser(description='Commands and options related to data display, listing.')
exclusive_group = parser.add_mutually_exclusive_group()
exclusive_sub_group = parser.add_argument_group()

#Option: details for infrastructure
exclusive_group.add_argument('-di','--infradetails', type=str, metavar='INFRA_ID', help='show details of a given infrastructure')
#Option: list infrastructures
exclusive_group.add_argument('-i','--infrastructures', action='store_true', help='list known infrastructures')
#Option: list nodes
exclusive_group.add_argument('-n','--nodes', action='store_true', help='list known nodes')
#Option: list tracked infrastructure-application pairs
exclusive_group.add_argument('-a','--applications', action='store_true', help='list tracked infrastructure-application pairs')

#Suboption: node details
exclusive_sub_group.add_argument('-dn','--nodedetails', type=str, metavar='NODE_ID', help='show details of a given node in a given infrastucture')

#Argparse
args = parser.parse_args()

if __name__ == "__main__":
    # -i: List infrastructures
    if (args.infrastructures == True):
        mstep_logger.List_all_infras()
    # -n: List nodes
    elif (args.nodes == True):
        mstep_logger.List_all_nodes()
    elif (args.applications == True):
        mstep_logger.List_all_infra_app_pairs()

    # -di and -dn: Infrastructure and node details
    elif args.infradetails != None:
        if args.nodedetails != None:
            logger.info('Details for node:')
            mstep_logger.Print_node(args.infradetails, args.nodedetails)
        else:
            mstep_logger.Print_infra(args.infradetails)
    elif args.nodedetails != None:
        print('*** Use "-dn" with option "-di"!')