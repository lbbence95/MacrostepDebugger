# Occopus related implementation of controller.orchestratorhandler.orchestratorhandler

import data.repository as mstep_repo
import json, os, re, subprocess, sys, time
import logging
#from subprocess import CREATE_NO_WINDOW, PIPE, STDOUT
import subprocess

#Logger setup
logger = logging.getLogger('terraform_handler')
logger.propagate = False
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
formatter = logging.Formatter('*** (%(asctime)s): %(message)s', "%Y-%m-%d %H:%M:%S")
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

class TerraformHandler():
    
    def __init__(self, orch_type):
        self.orch_type = orch_type
        self.app_regex = re.compile(".*\${.*_private_ip\}.*")

    def Check_infrastructure_descriptor(self, infra_folder):
        """

        Args:
            : .
        
        Returns:
            boolean: True if the descriptor is valid, False if not.
        """

        # Check if given folder exists

        if (os.path.exists(infra_folder) == True):
            # TO-DO: Actual validation of the infrastructure files.
            # Terraform validate or Terraform plan
            # Check output for errors
            return True
        else:
            return False
  
    def Get_processes_from_infrastructure_descriptor(self, infra_folder):
        """Examines a given folder for VM/process names.

        Args:
            infra_folder (string): A folder that contains the Terraform configuration files.
        
        Returns:
            list: A list of process (VM) names the infrastructure contains or an empty list if an error has occured.
        """

        infra_processes = []

        # Check the mstep_locals.tf file for vm names
        
        mstep_locals_file = os.path.join(infra_folder, 'mstep_locals.tf')

        if (os.path.exists(mstep_locals_file) == True):
            # For now, processes are enumerated in the first line of the mstep_locals.tf file
            # TO-DO: Get process names directly from the locals block

            processes=open(mstep_locals_file).readline().rstrip().lstrip('#').split(',')
            return processes

        else:
            logger.warning('"mstep_locals.tf" file not found.')
            return []
    
    def Start_infrastructure_instance(self, app):
        """Starts an infrastructure instance using the given application.

        Args:
            app (Application): An Application.
        
        Returns:
            string: An instance ID created by Terraform.
        """

        infra_id = ""

        logger.info('Creating instance...')

        #TO-DO: platform dependent code / independent instruction
        # Linux
        # terraform_subproc = subprocess.Popen('terraform apply -auto-approve', shell=True, cwd=app.infra_file, stdout=subprocess.PIPE, stderr=STDOUT)
        # Win
        terraform_subproc = subprocess.Popen('terraform apply -auto-approve', shell=False, cwd=app.infra_file, creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        while True:
            line = terraform_subproc.stdout.readline()
            
            if '.infra_id: Creation complete' in bytes.decode(line):
                infra_id = re.search(r"\=.*\]", bytes.decode(line.strip())).group(0).lstrip('=').rstrip(']')
                logger.info('Instance ID created by {}: {}'.format(app.orch.upper(), infra_id))
                break
            if not line: break

        if infra_id == '':
            logger.warning('Error: No ID created! Exiting...')
            sys.exit(0)
        
        return infra_id

    def Destroy_infrastrucure_instance(self, app, instance_id):

        # Issue the teardown of the infrastructure instance
        logger.info('Destroying "{} / {}"....'.format(app.app_name, instance_id))

        #TO-DO: platform dependent code / independent instruction
        # Linux
        # terraform_subproc = subprocess.run('terraform destroy -auto-approve', shell=True, cwd=app.infra_file, stdout=subprocess.PIPE, stderr=STDOUT)
        # Win
        terraform_subproc = subprocess.run('terraform destroy -auto-approve', shell=False, cwd=app.infra_file, creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        #TO-DO: Check if any error has occured
        logger.info('Instance successfully destroyed!')
    
    def Check_process_states(self, app, instance_id):
        """This function periodically checks infrastructure instance states, whether or not every VM started by the orchestrator is also registered within the debugger.

        Args:
            app (Application): An Application instance.
            instance_id (string): An infrastructure instance ID.
        """

        # Check state file for (node) process IDs
        # Collect (node) process IDs in state file
        # Check if each process has reached its first breakpoint, aka. ready

        logger.info('Waiting for Terraform to start processes (VMs)...')

        time.sleep(10)

        process_ids = []
        resources_list = []

        while (True):

            try:
                tf_state_file = json.loads(open(os.path.join(app.infra_file, 'terraform.tfstate')).read())
                resources_list = tf_state_file['resources']
                break
            except PermissionError:
                time.sleep(15)  
        
        for act_resource in resources_list:
            try:
                instances = act_resource['instances']
                for act_instance in instances:
                    process_ids.append(act_instance['attributes']['vars']['node_id'])
            except KeyError:
                pass

        #print('TEST: process_ids to wait for: {}'.format(process_ids))

        # Check every process is ready
        logger.info('Checking for root state...')
        
        infra_up = False
        db_processes = []

        while (infra_up == False):

            db_processes = mstep_repo.Read_nodes_from_infra(instance_id)
            
            if (db_processes != None):
                db_process_ids = [proc.node_id for proc in db_processes]

                for act_proc in process_ids:
                    if act_proc not in db_process_ids:
                        #TO-DO: wait for all processes
                        break
                
                    infra_up = True
            
            time.sleep(5)
        
        #TO-DO: more info on started processes
            
        logger.info('Instance reached root state!')
        logger.info('Running processes:\r\n')

        for act_proc in db_processes:
            print('\t "{}" ("{}")'.format(act_proc.node_name, act_proc.node_id))

        print('')

        return