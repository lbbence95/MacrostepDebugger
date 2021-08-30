# Represents the controller module of the debugger

import data.repository as mstep_repo
import util.logger as mstep_logger
import controller.exectree as mstep_exectree
import controller.orchestratorhandler.orch_factory as mstep_orch_factory
import json, logging, os.path, time, yaml

#Logger setup
logger = logging.getLogger('controller')
logger.propagate = False
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
formatter = logging.Formatter('*** (%(asctime)s): %(message)s', "%Y-%m-%d %H:%M:%S")
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

# Main functions
def Process_app_descriptor(app_desc_file):
    """This function processes the given application desriptor file.

    Args:
        app_desc_file (str): An application descriptor file's URI.
    """

    app_desc = os.path.join('infra_defs', app_desc_file)
    if (os.path.exists(app_desc) == True):
        app_desc_ok = False
        infra_desc_ok = False
        app_data = None
        infra_desc_file = None

        try:
            app_data = yaml.safe_load(open(app_desc))
            
            if all (k in app_data for k in ("application_name", "orchestrator")):
                               
                app_desc_ok = True
                orch = mstep_orch_factory.GetOrchHandler(app_data['orchestrator']['type'])

                # Occopus
                if (app_data['orchestrator']['type'] == 'occopus'):

                    infra_desc_file = os.path.join('infra_defs', app_data['orchestrator']['occopus']['infra_file'])
                    logger.info('Valid application descriptor file!')

                    if (orch.Check_infrastructure_descriptor(infra_desc_file) == True):
                        logger.info('Valid infrastructure descriptor file!')
                        infra_desc_ok = True

                    else:
                        logger.info('Invalid infrastructure descriptor file!')

                # Terraform
                elif (app_data['orch'] == 'terraform'):
                    print('Not implemented yet.')
            else:
                raise KeyError               

        except yaml.scanner.ScannerError:
            logger.info('Invalid application descriptor file!')
        except KeyError:
            logger.info('Invalid application descriptor file!')
        except TypeError:
            logger.info('Invalid infrastructure descriptor file!')

        if ((app_desc_ok and infra_desc_ok) == True):
            app_data['processes'] = json.dumps(orch.Get_processes_from_infrastructure_descriptor(infra_desc_file))

            mstep_repo.Register_new_application(app_data)
    else:
        logger.info('"{}" application descriptor does not exist!'.format(app_desc))


def Start_infra_instance(app):
    """Starts an infastructure instance of the given application. This function will return after the applciation instance reached root state.

    Args:
        app (Application): An Application instance.

    Returns:
        str: The created application instance's (infrastructure's) ID. Otherwise an empty string ("").
    """

    #TO-DO: handle connection errors

    orch_handler = mstep_orch_factory.GetOrchHandler(app.orch)

    instance_infra_id = orch_handler.Start_infrastructure_instance(app)

    if (instance_infra_id != ""):
        mstep_repo.Register_new_infrastructure(app.app_name, instance_infra_id)
        
        orch_handler.Check_process_states(app, instance_infra_id)

        if (mstep_repo.Is_infra_in_root_state(instance_infra_id) == True):
            logger.info('"{} / {}" reached root state.'.format(app.app_name, instance_infra_id))

            app_proc_names = sorted(json.loads(app.processes))

            app_instance_proc_names = []

            processes = mstep_repo.Read_nodes_from_infra(instance_infra_id)

            for act_process in processes:
                app_instance_proc_names.append(act_process.node_name)
            
            app_instance_proc_names = sorted(list(set(app_instance_proc_names)))

            if (app_instance_proc_names != app_proc_names):
                Stop_debugging_infra(app.app_name, instance_infra_id)
                return ""

            root_id = mstep_exectree.Get_root_id_for_application(app)

            if (root_id == ""):
                logger.info('No root collective breakpoint exists for app. "{}". Creating root...'.format(app.app_name))

                process_states = mstep_repo.Get_global_state_for_infra(instance_infra_id)
                root_id = mstep_exectree.Create_root(app, instance_infra_id, process_states)

                logger.info('Root collective breakpoint "{}" created for applciation "{}".'.format(root_id, app.app_name))

                mstep_repo.Update_app_root_collective_breakpoint(app.app_name, root_id)
            else:
                logger.info('Root collective breakpoint already exists for app. "{}".'.format(app.app_name))

                if (root_id != app.root_coll_bp):
                    logger.info('Root ID mismatch! Updating local root ID!')
                    mstep_repo.Update_app_root_collective_breakpoint(app.app_name, root_id)
                else:
                    logger.info('Root ID consistent!')          
            
            mstep_repo.Update_instance_current_collective_breakpoint(instance_infra_id, root_id)
            mstep_exectree.Update_node_app_instance_ids(app, root_id, instance_infra_id)

            mstep_repo.Update_app_current_collective_breakpoint(app.app_name, root_id)

            return instance_infra_id
    else:
        logger.info('Connection error.')
        return ""


def Stop_debugging_infra(app_name, infra_id):
    """Destroys the given infrastructure instance of the given application.

    Args:
        app_name (str): An application name.
        infra_id (str): An infrastructure ID.
    """

    if ((mstep_repo.App_exists(app_name) == True) and (mstep_repo.Infra_exists(infra_id) == True)):

        logger.info('Destroying instance in 5 seconds...')
        time.sleep(5)

        app = mstep_repo.Read_given_application(app_name)

        orch_handler = mstep_orch_factory.GetOrchHandler(app.orch)
        orch_handler.Destroy_infrastrucure_instance(app, infra_id)
    else:
        logger.info('Application "{}" or infrastructure "{}" does not exist!'.format(app_name, infra_id))


def Start_automatic_debug_session(app_name):
    """Start an automatic debugging session for the given application.

    Args:
        app_name (str): An application name.
    """

    if (mstep_repo.App_exists(app_name) == True):
        app = mstep_repo.Read_given_application(app_name)
        replay_pointer = ""
        root_exhausted = mstep_exectree.Is_app_root_exhausted(app)

        while (root_exhausted != True):

            app = mstep_repo.Read_given_application(app_name)

            # TO-DO: check if execution tree is partially exhausted or not.
            # TO-DO: select appropriate coll. bp. to continue automatic debugging from
        
            instance_id = ""

            if  (replay_pointer == ""):
                instance_id = Start_infra_instance(app)           
            else:
                instance_id = Replay_app_to_state(app.app_name, replay_pointer, keep_instance=True, continue_manual=False)        

            app_instance = mstep_repo.Read_given_infrastructure(instance_id)

            finished = False
            while (finished == False):

                process_to_step = Get_process_to_step_auto_debug(app, app_instance)

                logger.info('Stepping process: "{} / {}"\r\n'.format(instance_id, process_to_step))
                mstep_repo.Update_node_step_permission(app_instance.infra_id, process_to_step)
                mstep_logger.List_nodes_in_infra(app_instance.infra_id)

                logger.info('Waiting for instance to reach consistent global state...')
                while (mstep_repo.Is_infra_in_consistent_global_state(instance_id) == False):
                    time.sleep(5)

                logger.info('Consistent global state reached!\r\n')
                mstep_logger.List_nodes_in_infra(instance_id)

                process_states = mstep_repo.Get_global_state_for_infra(instance_id)
                app_instance = mstep_repo.Read_given_infrastructure(instance_id)

                next_coll_bp_id = mstep_exectree.Does_current_state_exist(app, app_instance, process_states)

                if (next_coll_bp_id != ""):
                    logger.info('Current state already exists ({}).'.format(next_coll_bp_id))
                else:
                    next_coll_bp_id = mstep_exectree.Create_collective_breakpoint(app, app_instance, process_states)
                    logger.info('New collective breakpoint created ({}).'.format(next_coll_bp_id))

                mstep_repo.Update_instance_current_collective_breakpoint(instance_id, next_coll_bp_id)
                mstep_exectree.Update_node_app_instance_ids(app, next_coll_bp_id, instance_id)

                app_instance = mstep_repo.Read_given_infrastructure(instance_id)

                if (app_instance.finished == 1):
                    finished = 1

            app = mstep_repo.Read_given_application(app.app_name)
            app_instance = mstep_repo.Read_given_infrastructure(instance_id)
            process_states = mstep_repo.Get_global_state_for_infra(instance_id)           
            mstep_exectree.Update_closest_alternative_coll_bp(app, app_instance.curr_coll_bp, process_states)

            replay_pointer = mstep_exectree.Get_closest_non_exhausted_parent(app, app_instance.curr_coll_bp, process_states)
            Stop_debugging_infra(app.app_name, app_instance.infra_id)

            root_exhausted = mstep_exectree.Is_app_root_exhausted(app.app_name)

            time.sleep(5)    
        logger.info('Automatic debug session finished!')
        
    else:
        logger.info('Application "{}" does not exist.'.format(app_name))


def Start_manual_debug_session(app_name):
    """Starts a manual debugging session for the given application.

    Args:
        app_name (str): An application name.
    """
    
    if (mstep_repo.App_exists(app_name) == True):

        app = mstep_repo.Read_given_application(app_name)

        instance_id = Start_infra_instance(app)

        if (instance_id == ""):
            logger.info('Some error has occured during application instance creation...')
            return

        while (mstep_repo.Read_given_infrastructure(instance_id).finished == 0):

            step_ok = False

            while (step_ok == False):

                process_to_step = str(input('Enter a non-finished process (VM) ID to step: '))

                if (mstep_repo.Node_exists(instance_id, process_to_step) == True and mstep_repo.Read_given_node(instance_id, process_to_step).finished == 0):
                    step_ok = True

            logger.info('Stepping process: "{} / {}"\r\n'.format(instance_id, process_to_step))

            mstep_repo.Update_node_step_permission(instance_id, process_to_step)

            mstep_logger.List_nodes_in_infra(instance_id)

            logger.info('Waiting for instance to reach consistent global state...')
            while (mstep_repo.Is_infra_in_consistent_global_state(instance_id) == False):
                time.sleep(5)
            
            logger.info('Consistent global state reached!\r\n')
            mstep_logger.List_nodes_in_infra(instance_id)

            process_states = mstep_repo.Get_global_state_for_infra(instance_id)
            app_instance = mstep_repo.Read_given_infrastructure(instance_id)

            next_coll_bp_id = mstep_exectree.Does_current_state_exist(app, app_instance, process_states)

            if (next_coll_bp_id != ""):
                logger.info('Current state already exists ({}).'.format(next_coll_bp_id))
            else:
                next_coll_bp_id = mstep_exectree.Create_collective_breakpoint(app, app_instance, process_states)
                logger.info('Current state does not exist in execution tree, new collective breakpoint created ({}).'.format(next_coll_bp_id))

                app_instance = mstep_repo.Read_given_infrastructure(instance_id)

                if (app_instance.finished == 1):
                    app = mstep_repo.Read_given_application(app.app_name)
                    mstep_exectree.Update_closest_alternative_coll_bp(app, next_coll_bp_id, process_states)

            mstep_repo.Update_instance_current_collective_breakpoint(instance_id, next_coll_bp_id)
            mstep_exectree.Update_node_app_instance_ids(app, next_coll_bp_id, instance_id)
     
        logger.info('Instance {} finished deployment!'.format(instance_id))

        Stop_debugging_infra(app.app_name, instance_id)
    else:
        logger.info('Application "{}" does not exist.'.format(app_name))


def Replay_app_to_state(app_name, target_coll_bp_id, keep_instance=False, continue_manual=True):
    """Replays the given application to the given global state.  

    Args:
        app_name (str): An application name.
        target_coll_bp_id (string): A target collective breakpoint ID in the execution tree, representing the desired global state.
        keep_instance (bool, optional): Keep the created instance after replay phase is complete. Defaults to False.
        continue_manual (bool, optional): Continue manual deployment after replay phase is complete. Defaults to True.
    Returns:
        str
    """

    if (mstep_repo.App_exists(app_name) == True):

        app = mstep_repo.Read_given_application(app_name)

        if (mstep_exectree.Does_coll_bp_exist(app, target_coll_bp_id) == True):

            logger.info('Given collective breakpoint exists.')

            instance_id = Start_infra_instance(app)

            if (instance_id != ""):
                curr_process_states = json.dumps(mstep_repo.Get_global_state_for_infra(instance_id))
                target_process_states = mstep_exectree.Get_process_states_of_coll_bp(app, target_coll_bp_id)

                while (curr_process_states != target_process_states):

                    logger.info('Target state not reached yet...')
                    
                    app_instance = mstep_repo.Read_given_infrastructure(instance_id)

                    next_coll_bp_id = mstep_exectree.Get_next_coll_bp_id_to_target(app, app_instance.curr_coll_bp, target_coll_bp_id)
                    next_process_states = mstep_exectree.Get_process_states_of_coll_bp(app, next_coll_bp_id)

                    logger.info('Next coll. bp.: {}'.format(next_coll_bp_id))

                    print('\r\nCurrent state:\r\n{}\r\n'.format(curr_process_states))
                    print('Targeted state:\r\n{}\r\n'.format(target_process_states))
                    print('Next state:\r\n{}\r\n'.format(next_process_states))

                    process_to_step = mstep_repo.Read_given_node(app_instance.infra_id, Get_proc_id_to_step(app_instance.infra_id, curr_process_states, next_process_states))

                    print('Process to step: {} ("{}")\r\n'.format(process_to_step.node_id, process_to_step.node_name))

                    logger.info('Stepping process: "{} / {}"\r\n'.format(app_instance.infra_id, process_to_step.node_id))
                    Step_given_node(app_instance.infra_id, process_to_step.node_id, silent=True)

                    logger.info('Waiting for instance to reach consistent global state...')
                    while (mstep_repo.Is_infra_in_consistent_global_state(app_instance.infra_id) == False):
                        time.sleep(5)

                    mstep_repo.Update_instance_current_collective_breakpoint(app_instance.infra_id, next_coll_bp_id)
                    mstep_exectree.Update_node_app_instance_ids(app, next_coll_bp_id, instance_id)
                    curr_process_states = json.dumps(mstep_repo.Get_global_state_for_infra(instance_id))

                    logger.info('Consistent global state reached.\r\n')
                    mstep_logger.List_nodes_in_infra(app_instance.infra_id)

                    time.sleep(2)
            
                logger.info('Target state reached!')

                app_instance = mstep_repo.Read_given_infrastructure(instance_id)

                if (app_instance.finished == 0):

                    cont_deploy = ""
                    
                    if (continue_manual == True):
                        cont_deploy = "y"
                    elif (continue_manual == False):
                        cont_deploy == "n"

                    if (cont_deploy.lower() == 'y'):

                        while (mstep_repo.Read_given_infrastructure(instance_id).finished == 0):
                            step_ok = False
                            while (step_ok == False):
                                process_to_step = str(input('Enter a non-finished process (VM) ID to step: '))
                                if (mstep_repo.Node_exists(instance_id, process_to_step) == True and mstep_repo.Read_given_node(instance_id, process_to_step).finished == 0):
                                    step_ok = True
                            
                            logger.info('Stepping process: "{} / {}"\r\n'.format(instance_id, process_to_step))

                            mstep_repo.Update_node_step_permission(instance_id, process_to_step)

                            mstep_logger.List_nodes_in_infra(instance_id)

                            logger.info('Waiting for instance to reach consistent global state...')
                            while (mstep_repo.Is_infra_in_consistent_global_state(instance_id) == False):
                                time.sleep(5)  

                            logger.info('Consistent global state reached!\r\n')
                            mstep_logger.List_nodes_in_infra(instance_id)

                            process_states = mstep_repo.Get_global_state_for_infra(instance_id)
                            app_instance = mstep_repo.Read_given_infrastructure(instance_id)

                            next_coll_bp_id = mstep_exectree.Does_current_state_exist(app, app_instance, process_states)

                            if (next_coll_bp_id != ""):
                                logger.info('Current state already exists ({}).'.format(next_coll_bp_id))
                            else:
                                next_coll_bp_id = mstep_exectree.Create_collective_breakpoint(app, app_instance, process_states)
                                logger.info('Current state does not exist in execution tree, new collective breakpoint created ({}).'.format(next_coll_bp_id))

                                app_instance = mstep_repo.Read_given_infrastructure(instance_id)

                                if (app_instance.finished == 1):
                                    mstep_exectree.Update_closest_alternative_coll_bp(app, next_coll_bp_id, process_states)

                            mstep_repo.Update_instance_current_collective_breakpoint(instance_id, next_coll_bp_id)
                            mstep_exectree.Update_node_app_instance_ids(app, next_coll_bp_id, instance_id)
                        
                        logger.info('Instance {} finished deployment!'.format(instance_id))

                        if (keep_instance == True):
                            logger.info('Instance "{} / {}" kept alive.'.format(app.app_name, instance_id))                         
                        else:
                            Stop_debugging_infra(app.app_name, instance_id)
                    else:
                        if (keep_instance == True):
                            logger.info('Instance "{} / {}" kept alive.'.format(app.app_name, instance_id))
                        else:
                            Stop_debugging_infra(app.app_name, instance_id)
                    
                    return instance_id
                else:
                    if (keep_instance == True):
                        logger.info('Instance "{} / {}" kept alive.'.format(app.app_name, instance_id))
                    else:
                        Stop_debugging_infra(app.app_name, instance_id)
                    
                    return instance_id
            else:
                logger.error('Some error has occured during application instance creation...')
        else:
            logger.warning('Given collective breakpoint does not exist.')
    else:
        logger.info('Application "{}" does not exists.'.format(app_name))


def Step_given_node(infra_id, node_id, silent=False):
    """Permits the given node to move to the next breakpoint.

    Args:
       infra_id (string): An infrastructure ID.
       node_id (string): A list of node IDs.
       silent (bool, optional): Suppress console messages if stepping was OK. Defaults to False.
    """

    if (mstep_repo.Node_exists(infra_id, node_id) == True):
        act_node = mstep_repo.Read_given_node(infra_id, node_id)
        if (act_node.finished == 0):
            mstep_repo.Update_node_step_permission(act_node.infra_id, act_node.node_id)
            if (silent == False):
                mstep_logger.Print_infrastructure_details(infra_id)
        else:           
            logger.info('Node "{}" ({}) has already finished.'.format(node_id, act_node.node_name))
    else:
        logger.info('No such node as "{}/{}".'.format(infra_id, node_id))


def Get_process_to_step_auto_debug(app, app_instance, selection_policy="abc"):
    """Using the current collective breakpoint the instance is at, this function returns a process ID.

    Args:
        app (Application): An Application.
        app_instance (Infrastructure): An application instance (Infrastructure).
        selection_policy (str, optional): A selection policy to influence process selection (e.g. "ABC" order). Defaults to "abc".
    Returns:
        str: A process ID.
    """

    processes = list(sorted(mstep_repo.Read_nodes_from_infra(app_instance.infra_id), key=lambda x: (x.node_name, x.node_id), reverse=False))
    num_unfinished = mstep_repo.How_many_processes_havent_finished(app_instance.infra_id)

    if (num_unfinished == 1):      
        for act_proc in processes:
            if act_proc.finished == 0: return act_proc.node_id
    else: 
        child_nodes = mstep_exectree.Get_list_of_children_nodes(app, app_instance.curr_coll_bp)

        # This is ABC
        if (len(child_nodes) == 0):       
            for act_proc in processes:
                if act_proc.finished == 0: return act_proc.node_id
        else:
            traversed_states = []
            for act_child in child_nodes:
                traversed_states.append(json.loads(mstep_exectree.Get_process_states_of_coll_bp(app, act_child)))

            i = 0
            j = 0
            proc_name = processes[0].node_name
            
            for act_proc in processes:
                if (act_proc.finished == 0):
                    test_state = json.loads(json.dumps(mstep_repo.Get_global_state_for_infra(app_instance.infra_id)))
                    test_state[act_proc.node_name][i] += 1

                    if (test_state not in traversed_states):
                        return act_proc.node_id

                i += 1
                j += 1

                if ((j < len(processes)) and (proc_name != processes[j].node_name)):
                    proc_name = processes[j].node_name
                    i = 0
 

def Get_proc_id_to_step(app_instance_id, curr_process_states, next_process_states):
    """Gets the ID of the process that needs to be stepped.

    Args:
        app_instance_id (string): An application instance (infrastructure) ID.
        curr_process_states (string): A JSON string defining a current global state.
        next_process_states (string): A JSON string defining the next global state.

    Returns:
        string: A process (e.g. VM) ID or an empty string if the states are the same.
    """

    json_curr = json.loads(curr_process_states)
    json_next = json.loads(next_process_states)

    for proc_name in json_next:

        i = 0

        while (i < len(json_next[proc_name])):
            if (json_curr[proc_name][i] != json_next[proc_name][i]):             
                processes = sorted(list(filter(lambda x: x.node_name == proc_name, mstep_repo.Read_nodes_from_infra(app_instance_id))), key=lambda y: y.node_id, reverse=False)
                return processes[i].node_id

            i += 1
    

def Step_whole_infra(infra_id):
    """Permits all nodes in the given infrastructure to move to the next breakpoint.

    Args:
        infra_id (string): An infrastructure ID.
    """
    if (mstep_repo.Infra_exists(infra_id) == True):
        infra_nodes = mstep_repo.Read_nodes_from_infra(infra_id)

        for act_node in infra_nodes:
            mstep_repo.Update_node_step_permission(infra_id, act_node.node_id)


# Aux. Functions, methods
def Initialize():
    """Initializes a new database.
    """

    if (os.path.exists(os.path.join('data','mstepDB.db'))):
        logger.info('Local database: exists.')
    else:
        logger.warning('Local database: does not exist.')
        mstep_repo.Initialize_db()


def Clear_database():
    """Clears the current database.
    """
    mstep_repo.Initialize_db()