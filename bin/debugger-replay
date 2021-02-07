#!/usr/bin/env python

#CLI functions related to replaying an execution-path.

from controller import controller as mstep_controller
from util import logger as mstep_logger
import argparse, logging, os.path, requests, time, json

#Logger setup
logger = logging.getLogger('debugger_replay')
logger.propagate = False
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
formatter = logging.Formatter('*** (%(asctime)s): %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

#Options and suboptions
parser = argparse.ArgumentParser(description='Commands and options related to replaying an execution-path.')
#exclusive_group = parser.add_mutually_exclusive_group()
arg_group = parser.add_argument_group()

#Option: define application
arg_group.add_argument('-a', '--application', type=str, metavar='APPLICATION_NAME', nargs=1, required=True, help='an application name on which replaying is executed')

#Option: define state, collective breakpoint
arg_group.add_argument('-s', '--state', type=str, metavar='COLLECTIVE_BREAKPOINT_ID', nargs=1, required=True, help='a collective breakpoint that identifies a global state')

#Option: define infrastructure description file
arg_group.add_argument('-f', '--file', type=str, metavar='FILE', nargs=1, required=True, help='an infrastructure description file in the format used by the Occopus cloud-orchestrator')

#Option: define orchestrator location
arg_group.add_argument('-o', '--orchestrator', metavar='ORCHESTRATOR_URL', type=str, nargs=1, required=True, help='an URL where the orchestrator is available (currently supported: Occopus)')

#Argparse
args = parser.parse_args()

if __name__ == "__main__":
    if ((args.application != None) and (args.state != None) and (args.orchestrator != None)):
        if (os.path.exists(os.path.join('infra_defs', args.file[0])) == True):
            app_file = str(os.path.join('infra_defs', args.file[0]))

            mstep_controller.Replay_infrastructure_to_state_Occo(args.application[0], args.state[0], app_file, args.orchestrator[0])
        else:
            logger.info('Given infrastructure description file not found!')
    elif ((args.state != None) or (args.application == None) or (args.orchestrator == None) or args.file == None):
        print('*** Required arguments: "-a", "-s", "-f", "-o".')