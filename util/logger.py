# Represents logging functions

from data import repository as mstep_repo
import logging

#Logger setup
logger = logging.getLogger('logger')
logger.propagate = False
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
formatter = logging.Formatter('*** (%(asctime)s): %(message)s', "%Y-%m-%d %H:%M:%S")
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

#List all applications
def List_all_applications():
    """Prints a list of managed/known applications.
    """

    logger.info('Listing known applications...')

    applications = sorted(mstep_repo.Read_all_application(), key=lambda x: x.creation_date)

    if (len(applications) == 0):
        logger.info('No managed applications.')
    else:
        logger.info('Managed applications:')
        for act_app in applications:
            print('"{}" ("{}")'.format(act_app.app_name, act_app.orch.upper()))

#List one application
def List_one_application(app_name):
    """Prints details for a given application.txt

    Args:
        app_name (string): An application name.
    """

    logger.info('Listing details for application "{}"...'.format(app_name))

    application = mstep_repo.Read_given_application(app_name)

    if (application != None):
        print('\r\n"{}" registered at : "{}"\r\norch.: "{}", orch. URI: "{}",\r\ninfra. descriptor: "{}"\r\n\nApp. process types: {}\r\n\nRoot ID: "{}"\r\n'
        .format(application.app_name, application.creation_date.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 
        application.orch.upper(), application.orch_loc, application.infra_file, application.processes, application.root_coll_bp, application.curr_coll_bp))

        # TO-DO: list instance informations as well

        infra_instances = mstep_repo.Read_all_instance_for_given_application(app_name)

        try:
            print('Instances: {}'.format(len(infra_instances)))
        except TypeError:
            print('Instances: 0')

        if (infra_instances != None):
            for act_instance in infra_instances:
                print(act_instance.infra_id)
    else:
        logger.info('No such application.')

def List_all_infras():
    """Prints a list of managed infrastructures.
    """

    logger.info('Listing managed infrastructures:')

    infras = sorted(mstep_repo.Read_all_infrastructure(), key=lambda x: x.app_name)
    if (len(infras) == 0):
        logger.info('No managed infrastructures!')
    else:
        logger.info('Managed infrastructures:')
        for act_infra in infras:
            print('({}) "{}" registered at {}'.format(act_infra.app_name, act_infra.infra_id, act_infra.registration_date.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]))

def List_nodes_in_infra(infra_id):
    """Lists all nodes in a given infrastructure.

    Args:
        infra_id (string): An infrastructure ID.
    """

    nodes = sorted(mstep_repo.Read_nodes_from_infra(infra_id), key=lambda x: (x.node_name, x.node_id))

    if (len(nodes) == 0):
        logger.info('No processes in infrastructure')
    else:
        for act_node in nodes:
            if (act_node.move_next == 1):
                print('->\t"{}" ("{}"), at bp.: #{}, finished: {}, permitted: {} ({})'.format(act_node.node_name, act_node.node_id, act_node.curr_bp,
                'Yes' if act_node.finished == 1 else 'No', 'Yes' if act_node.move_next == 1 else 'No', act_node.refreshed))
            else:
                print('\t"{}" ("{}"), at bp.: #{}, finished: {}, permitted: {} ({})'.format(act_node.node_name, act_node.node_id, act_node.curr_bp,
                'Yes' if act_node.finished == 1 else 'No', 'Yes' if act_node.move_next == 1 else 'No', act_node.refreshed))
        
        print('')

def List_all_nodes():
    """Prints a list of managed nodes.
    """
    
    logger.info('Listing managed nodes:')

    nodes = sorted(mstep_repo.Read_all_node(), key=lambda x: (x.infra_id, x.node_id))
    if (len(nodes) == 0):
        logger.info('No managed nodes!')
    else:
        logger.info('Managed nodes:')
        for act_node in nodes:
            last_bp = mstep_repo.Read_given_nodes_breakpoint(act_node.infra_id, act_node.node_id)[-1]
            print('"{}"/"{}" registered at {}, at breakpoint #{} (tags: {})\r\nFinsished: {}'.
            format(act_node.infra_id, act_node.node_id, act_node.registered.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], act_node.curr_bp, last_bp.bp_tag, 'Yes' if act_node.finished == 1 else 'No'))

def Print_infrastructure_details(infra_id):
    """Prints the details of a single infrastructure.

    Args:
        infra_id (string): An infrastructure ID.
    """
    if (mstep_repo.Infra_exists(infra_id) == True):
        infra = mstep_repo.Read_given_infrastructure(infra_id)
            
        logger.info('Details for infrastructure "{}" ({}) registered at {}.\r\n\nFinished: {}\r\nCurr. coll. bp.: "{}"\r\n'.format(
            infra.infra_id, infra.infra_name, infra.registration_date.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 'Yes' if infra.finished == 1 else 'No', infra.curr_coll_bp))
            
        nodes = mstep_repo.Read_nodes_from_infra(infra_id)
        if (nodes != None):
            for act_node in nodes:
                print('"{}" ({}) at breakpoint #{}, permitted: {}, finished: {}'.format(act_node.node_id, act_node.node_name, act_node.curr_bp,
                'Yes' if act_node.move_next == 1 else 'No',
                'Yes' if act_node.finished == 1 else 'No'))
    else:
        logger.info('No such infrastructure!')

def Print_node_details(infra_id, node_id):
    """Prints the details of a single node.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.
    """

    node = mstep_repo.Read_given_node(infra_id, node_id)

    if (node == None):
        logger.info('No such node.')
    else:
        logger.info('Details for node: "{} / {}"'.format(infra_id, node_id))
        print('Infrastructure "{}"'.format(node.infra_id))
        print('Permitted: {}, Finished: {}'.format('Yes' if node.move_next == 1 else 'No', 'Yes' if node.finished == 1 else 'No'))
        print('Node public IP: "{}"'.format(node.public_ip))

        bps = mstep_repo.Read_given_nodes_breakpoint(infra_id, node_id)

        print('\r\nNode breakpoints:')

        for act_bp in bps:
            print('Breakpoint #{} reached at {} (tags: {})'.format(act_bp.bp_num, act_bp.bp_reg.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], act_bp.bp_tag))

def Print_breakpoint_info(request_data):
    """Prints the received VM data to the console.

    Args:
        request_data (request): A request containing a JSON string.
    """

    json_data = request_data.get_json()

    # Infrastructure related data
    infra_id = json_data['processData']['infraID']
    infra_name = json_data['processData']['infraName']
    node_id = json_data['processData']['nodeID']
    node_name = json_data['processData']['nodeName']
    bp_tag = json_data['processData']['bpTag']
  
    node_publicIP = request_data.remote_addr
    
    # User data
    node_data = json_data['userData']

    # Printing received information
    print('*** Infrastructure ID: {}'.format(infra_id))
    print('*** Infrastructure Name: {}'.format(infra_name))

    print('*** Node ID: {}'.format(node_id))
    print('*** Node Name: {}'.format(node_name))

    print('*** Breakpoint Tags: {}'.format(bp_tag))

    print('*** Node Data:')

    for dataKey in node_data:
        print('*** {}: {}'.format(dataKey, node_data[dataKey]))

    print('*** Node Public IP: {}\r\n'.format(node_publicIP))