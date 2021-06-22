# Abstract description of orchestrator handler functionalities.

class OrchestratorHandler():

    def __init__(self, orch_type):
        self.orch_type = orch_type

    def Check_infrastructure_descriptor(self, infra_desc):
        """Upon registering a new application, the included infrastructure descriptor file(s) have to be validated.
        This function should check the given descriptor whether they are syntactically and semantically correct.

        Args:
            infra_desc (string): An URI for the infrastructure descriptor.
        Returns:
            bool: True if syntactically and semantically correct, otherwise False.
        """
        pass
    
    def Get_processes_from_infrastructure_descriptor(self, infra_file):
        """Upon registering a new application, orchestrator handlers examine the included infrastructure descriptor(s) and collect process names/IDs. These names/IDs are needed, so that  
        the debugger knows about the processes it should control.

        Args:
            infra_file (string): An URI for the infrastructure descriptor.
        Returns:
            list: A list of process names/IDs. Esentially the processes the application is made up of.
        """
        pass

    def Check_process_statuses(self, app, instance_id):
        """The debugger receives state information from various processes, however it does not know how many processes it shall handle. 
        This function shall check if all processes in the application are running, be it virtual machines or other actual processes.

        Args:
            app (Application): An Application instance.
            instance_id (string): An infrastructure/instance ID of the given application.
        """
        pass

    def Start_infrastructure_instance(self, app):
        """Upon the start of a debugging session, be it manual or automatic, infrastructure instances must be started. 
        Infrastructure instances are requested by the debugger using orchestrator handlers. Once an instance is started, this method should return/display 
        an instance ID and the processes (e.g. VMs) the instance is made up from.

        Args:
            app (Application): An Application.
        Returns:
            string: An application instance ID if all processes in the application instance are running and reported their first breakpoint. 
            Otherwise, or in case of an error, an empty string ("").
        """
        pass

    def Destroy_infrastrucure_instance(self, app, instance_id):
        """When an execution path has been traversed, the used infrastructure instance may not be needed anymore, thus stopping or destroying it may be necessary.

        Args:
            app (Application): An Application.
            instance_id (string): An infrastructure ID.
        """
        pass