#!/usr/bin/env python

#Main, debugger related CLI functions

import api.rest as mstep_rest
import controller.controller as mstep_controller
import controller.exectree as mstep_exectree
import argparse, logging

#Logger setup
logger = logging.getLogger('debugger_app')
logger.propagate = False
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
formatter = logging.Formatter('*** (%(asctime)s): %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

#Options and suboptions
parser = argparse.ArgumentParser(description='General commands and options related to the macrostep debugger app.')
exclusive_group = parser.add_mutually_exclusive_group()
exclusive_sub_group = parser.add_mutually_exclusive_group()

#Option: Clear database
exclusive_group.add_argument('-c','--clear', action='store_true', help="clear the debugger's internal database")

#Option: Test Neo4j database connection
exclusive_group.add_argument('-n','--neo',action='store_true',help='test Neo4j database connection')

#Option: Start REST API
exclusive_group.add_argument('-s','--start', action='store_true', help='start the macrostep debugger REST API (default port: 5000)')

#Suboption: define port for REST API
exclusive_sub_group.add_argument('-p', '--port', type=int, metavar='PORT', help='define macrostep debugger service port')

#Argparse
args = parser.parse_args()

if __name__ == "__main__":
    
    # -c: Clear database
    if args.clear == True:
        mstep_controller.Clear_database()
        logger.info('Database records dropped!')
    
    # -s and -p: Service start and port
    elif args.start == True:
        if args.port != None:
            if int(args.port) and int(args.port) > 0 and int(args.port) <= 65535:
                mstep_controller.Initialize()
                mstep_rest.app.run(host = '0.0.0.0', port=int(args.port), debug = True, threaded=True)
            else:
                logger.info('Invalid port!')
        else:
            mstep_controller.Initialize()
            mstep_rest.app.run(host = '0.0.0.0', port=5000, debug = True, threaded=True)
    elif args.port != None:
        print('*** Use "-p" with option "-s"!')

    # -n: Test Neo4j database connection
    elif (args.neo == True):
        logger.info('Testing Neo4j database connection...')
        mstep_exectree.Read_connection_details()