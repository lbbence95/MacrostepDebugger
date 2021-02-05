#!/usr/bin/env python

#CLI functions related to infrastructure tracing or tracking

from controller import controller as mstep_controller
from controller import exectree as mstep_exectree
import argparse, logging

#Logger setup
logger = logging.getLogger('debugger_trace')
logger.propagate = False
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
formatter = logging.Formatter('*** (%(asctime)s): %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

#Options and suboptions
parser = argparse.ArgumentParser(description='Commands and options related to tracing or tracking.')
exclusive_group = parser.add_mutually_exclusive_group()
exclusive_sub_group = parser.add_mutually_exclusive_group()

#Option: trace, stop tracing infrastructure
exclusive_group.add_argument('-t', '--trace', type=str, metavar='INFRA_ID', nargs=1, help='a(n ochestrator) given infrastrucutre ID to trace')
exclusive_group.add_argument('-s', '--stoptrace', type=str, metavar='INFRA_ID', nargs=1, help='stop tracing the given infrastructure')

#Suboption: define application
exclusive_sub_group.add_argument('-a', '--application', type=str, metavar='APPLICATION_NAME', nargs=1, help='an application name on which macrostep-debugging is executed')

#Argparse
args = parser.parse_args()

if __name__ == "__main__":
    # -t and -a: Track infrastructure
    if (args.trace != None):
        if (args.application != None):
            if mstep_controller.Infra_exists(args.trace[0]):
                result = mstep_exectree.Infra_app_pair_root(args.trace[0], args.application[0])
                logger.info(result[1])
            else:
                logger.info('No infrastructure exists with ID "{}"!'.format(args.trace[0]))
        else:
            print('*** Use "-t" with option "-a"!')
    elif ((args.trace == None) and (args.application != None)):
        print('*** Use "-a" with option "-t"!')

    # -st: Stop tracking
    elif (args.stoptrace != None):
        if (mstep_controller.Infra_exists(args.stoptrace[0]) == True):
            mstep_exectree.Stop_tracing(args.stoptrace[0])
            logger.info('Stopped tracking infrastructure "{}".'.format(args.stoptrace[0]))
        else:
            print('*** No application-infrastructure pair exists with infrastructure ID "{}"!'.format(args.stoptrace[0]))
