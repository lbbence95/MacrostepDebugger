# Occopus related implementation of controller.orchestratorhandler.orchestratorhandler

import data.repository as mstep_repo
import sys, requests, os, time, yaml
import logging

#Logger setup
logger = logging.getLogger('occopus_handler')
logger.propagate = False
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
formatter = logging.Formatter('*** (%(asctime)s): %(message)s', "%Y-%m-%d %H:%M:%S")
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

class TerraformHandler():
    
    def __init__(self, orch_type):
        self.orch_type = orch_type

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
            return []
    
    def Start_infrastructure_instance(self, app):
        """Starts an infrastructure instance using the given application and related ....

        Args:
            app (Application): An Application.
        
        Returns:
            string: An instance ID returned created by Terraform.
        """

        return

    def Destroy_infrastrucure_instance(self, app, instance_id):
        return
    
    def Check_process_states(self, app, instance_id):
        """This function periodically checks infrastructure instance states, whether or not every VM started by the orchestrator is also registered within the debugger.

        Args:
            app (Application): An Application instance.
            instance_id (string): An infrastructure instance ID.
        """

        return