# Occopus related implementation of controller.orchestratorhandler.orchestratorhandler

import data.repository as mstep_repo
import sys, re, requests, time, yaml
import json, logging

#Logger setup
logger = logging.getLogger('occopus_handler')
logger.propagate = False
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
formatter = logging.Formatter('*** (%(asctime)s): %(message)s', "%Y-%m-%d %H:%M:%S")
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

class OccopusHandler():

    def __init__(self, orch_type):
        self.orch_type = orch_type
        self.app_regex = re.compile(".*\{getprivip\(.*\)\}.*")

    def Check_infrastructure_descriptor(self, infra_file):
        """Checks and validates a given infrastructure descriptor.

        Args:
            file (string): An Occopus infrastructure descriptor file.
        
        Returns:
            boolean: True if the descriptor is valid, False if not.
        """

        try:
            infra_desc = yaml.safe_load(open(infra_file))

            # TO-DO: Actual validation of the infrastructure descriptor file.

            return True
    
        except yaml.scanner.ScannerError:
            return False
        except FileNotFoundError:
            return False
    
    def Get_processes_from_infrastructure_descriptor(self, infra_file):
        """Examines a given infrastructure descriptor file for VM/process names.

        Args:
            infra_file (string): An Occopus infrastructure descriptor file.
        
        Returns:
            list: A list of process (VM) names the infrastructure contains or an empty list if an error has occured.
        """

        infra_processes = []

        try:
            infra_desc = yaml.safe_load(open(infra_file))

            nodes = infra_desc['nodes']

            for act_node in nodes:
                infra_processes.append(act_node['name'])
            
            return sorted(infra_processes)

        except yaml.scanner.ScannerError:
            return []
        except FileNotFoundError:
            return []

    def Start_infrastructure_instance(self, app):
        """Starts an infrastructure instance using the given application and its infrastructure desciptor.

        Args:
            app (Application): An Application.
        
        Returns:
            string: An instance ID returned by Occopus.
        """

        app_file = open(app.infra_file, 'rb')

        url_create_instance = app.orch_loc + '/infrastructures/'

        logger.info('Creating instance. Making request to "{}"'.format(url_create_instance))
      
        response = None
        instance_infra_id = ""

        #TO-DO: handle connection errors
        try:
            response = requests.post(url=url_create_instance, data=app_file)
            instance_infra_id = response.json()['infraid']
            logger.info('Instance ID created by {}: {}'.format(app.orch.upper(), instance_infra_id))
        except requests.exceptions.ConnectionError as conn_er:
            logger.info('Failed to establish connection!\r\n{}'.format(conn_er))
            sys.exit(1)
        except KeyError:
            logger.info('KeyError occured. Please check infrastructure descriptor file!')
            sys.exit(1)
        except json.decoder.JSONDecodeError:
            logger.info('An error has occured.')
            sys.exit(1)


        return str(instance_infra_id)

    def Destroy_infrastrucure_instance(self, app, instance_id):
        
        url_destroy = app.orch_loc + '/infrastructures/' + instance_id

        logger.info('Destroying "{} / {}"....'.format(app.app_name, instance_id))
        logger.info('Making request to "{}"'.format(url_destroy))

        response = requests.delete(url=url_destroy)

        if ('infraid' in response.json().keys()):
            logger.info('Instance successfully destroyed!')
        else:
            logger.info('Something went wrong. Instance may have already been destroyed.')

    def Check_process_states(self, app, instance_id):
        """This function periodically checks infrastructure instance states, whether or not every VM started by the orchestrator is also registered within the debugger.

        Args:
            app (Application): An Application instance.
            instance_id (string): An infrastructure instance ID.
        """
        
        url_status = app.orch_loc + '/infrastructures/' + instance_id

        # Contains process (aka. VMs) of the infrastructure instance
        # This dict represents VMs. Each VM has a node ID and whether or not it has already reported.

        processes = {}
        infra_up = False

        while (infra_up == False):
            print('')
            logger.info('Checking process states. Making request to "{}"'.format(url_status))

            # Get infrastructure status
            infra_status = requests.get(url=url_status).json()

            if (bool(infra_status) == False):
                # No VM started yet by orchestrator
                logger.info('Waiting for "{}" to start VMs...'.format(app.orch.upper()))
            else:
                # Some VMs have started, check if they have already reported

                vm_names = infra_status.keys()

                for act_vm_name in vm_names:

                    act_vm_ids = list(infra_status[act_vm_name]['instances'].keys())
                    for vm_id in act_vm_ids:
                        processes[vm_id] = mstep_repo.Node_exists(instance_id, vm_id)
                        logger.info('Waiting for VM: {} ("{}"), ready: {}'.format(vm_id, act_vm_name, 'Yes' if processes[vm_id] == True else 'No'))

                infra_up = True
                
                # Check if every VM is ready
                for act_vm_id in processes:
                    if (processes[act_vm_id] == False):
                        infra_up = False
                        break
                
                time.sleep(3)

                infra_status = requests.get(url=url_status).json()
                vm_names = infra_status.keys()
                for act_vm_name in vm_names:
                    act_vm_ids = list(infra_status[act_vm_name]['instances'].keys())
                    for vm_id in act_vm_ids:
                        processes[vm_id] = mstep_repo.Node_exists(instance_id, vm_id)
                        if (processes[vm_id] == False):
                            infra_up = False
                            break

            if (infra_up == True):
                #Instance up and running
                print('')
                logger.info('All processes in "{} / {}" are running.'.format(app.app_name, instance_id))

                nodes = sorted(mstep_repo.Read_nodes_from_infra(instance_id), key=lambda x: (x.node_name, x.node_id))

                print('')
                for act_node in nodes:
                    print('\t"{}" ("{}"), at bp.: #{}, finished: {}, permitted: {} ({})'.format(act_node.node_name, act_node.node_id, act_node.curr_bp,
                    'Yes' if act_node.finished == 1 else 'No', 'Yes' if act_node.move_next == 1 else 'No', act_node.refreshed))
                    
                print('')    
            else:
                #Instance not fully deployed, wait
                time.sleep(3)