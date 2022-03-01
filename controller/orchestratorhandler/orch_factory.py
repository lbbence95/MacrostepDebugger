import controller.orchestratorhandler.plugins.occopus_handler as occopus_handler
import controller.orchestratorhandler.plugins.terraform_handler as terraform_handler

def GetOrchHandler(orch_type):

    orch_name = orch_type.lower()

    if (orch_name == 'occopus'):
        return occopus_handler.OccopusHandler(orch_type)
    elif (orch_name == 'terraform'):
        return terraform_handler.TerraformHandler(orch_type)