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

    # Check application descriptor file
    app_desc = os.path.join('infra_defs', app_desc_file)
    if (os.path.exists(app_desc) == True):
        # File exists
        # Check for proper format and keys
        app_desc_ok = False
        infra_desc_ok = False
        app_data = None
        infra_desc_file = None

        try:
            # Load YAML file
            app_data = yaml.safe_load(open(app_desc))              
            
            # Check needed keys in app descriptor
            if all (k in app_data for k in ("app_name", "orch", "orch_uri")):
                               
                app_desc_ok = True
                orch = mstep_orch_factory.GetOrchHandler(app_data['orch'])

                # Check infra descriptor
                # Occopus
                if (app_data['orch'] == 'occopus'):

                    infra_desc_file = os.path.join('infra_defs', app_data['infra_file'])
                    logger.info('Valid application descriptor file!')

                    # Check if infrastructure file is valid
                    # TypeError if infra_desc_file is None
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
            # Get process names from infrastructure descriptor
            app_data['processes'] = json.dumps(orch.Get_processes_from_infrastructure_descriptor(infra_desc_file))

            # Descriptors ok, register new app
            mstep_repo.Register_new_application(app_data)

    else:
        # File does not exist, warn user
        logger.info('"{}" application descriptor does not exist!'.format(app_desc))


def Start_infra_instance(app):
    """Starts an infastructure instance of the given application. This function will return after the applciation instance reached root state.

    Args:
        app (Application): An Application instance.

    Returns:
        str: The created application instance's (infrastructure's) ID. Otherwise an empty string ("").
    """

    #TO-DO: handle connection errors

    # Start infrastructure instance using appropriate orchestrator handler
    orch_handler = mstep_orch_factory.GetOrchHandler(app.orch)

    # Get instance ID from orchestrator
    instance_infra_id = orch_handler.Start_infrastructure_instance(app)

    if (instance_infra_id != ""):
        # Register infrastructure
        mstep_repo.Register_new_infrastructure(app.app_name, instance_infra_id)
        
        # Check infra status, whether or not has every process reported
        orch_handler.Check_process_statuses(app, instance_infra_id)

        # Check if root state
        if (mstep_repo.Is_infra_in_root_state(instance_infra_id) == True):
            logger.info('"{} / {}" reached root state.'.format(app.app_name, instance_infra_id))

            # Check if every process type had reported
            app_proc_names = sorted(json.loads(app.processes))

            app_instance_proc_names = []

            processes = mstep_repo.Read_nodes_from_infra(instance_infra_id)

            for act_process in processes:
                app_instance_proc_names.append(act_process.node_name)
            
            app_instance_proc_names = sorted(list(set(app_instance_proc_names)))

            if (app_instance_proc_names != app_proc_names):
                # Error
                Stop_debugging_infra(app.app_name, instance_infra_id)
                return ""

            root_id = mstep_exectree.Get_root_id_for_application(app)

            # Check if root exists in Neo4j database
            if (root_id == ""):
                # Create root, none exists
                logger.info('No root collective breakpoint exists for app. "{}". Creating root...'.format(app.app_name))

                process_states = mstep_repo.Get_global_state_for_infra(instance_infra_id)
                root_id = mstep_exectree.Create_root(app, instance_infra_id, process_states)

                logger.info('Root collective breakpoint "{}" created for applciation "{}".'.format(root_id, app.app_name))

                # Update application root coll bp
                mstep_repo.Update_app_root_collective_breakpoint(app.app_name, root_id)
            else:
                # Root already exists
                logger.info('Root collective breakpoint already exists for app. "{}".'.format(app.app_name))

                if (root_id != app.root_coll_bp):
                    logger.info('Root ID mismatch! Updating local root ID!')
                    
                    # Update application root coll bp
                    mstep_repo.Update_app_root_collective_breakpoint(app.app_name, root_id)
                else:
                    logger.info('Root ID consistent!')          
            
            # Update (infrastructure) instance current collective breakpoint ID
            mstep_repo.Update_instance_current_collective_breakpoint(instance_infra_id, root_id)

            # Update application current_collective breakpoint ID
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

        # Application exists
        app = mstep_repo.Read_given_application(app_name)

        # Destroy infrastructure instance using appropriate orchestrator handler
        orch_handler = mstep_orch_factory.GetOrchHandler(app.orch)

        # Destroy infra
        orch_handler.Destroy_infrastrucure_instance(app, infra_id)
    else:
        logger.info('Application "{}" or infrastructure "{}" does not exist!'.format(app_name, infra_id))


def Start_automatic_debug_session(app_name):
    """Start an automatic debugging session for the given application.

    Args:
        app_name (str): An application name.
    """

    # Check if app exists
    if (mstep_repo.App_exists(app_name) == True):
        # Automatic debugging must continue until every possible execution path has been traversed.
        # This means that every collective breakpoint has been exhausted. In essence, automatic debugging must continue until the root collective breakpoint is exhausted as well.

        # Application exists
        app = mstep_repo.Read_given_application(app_name)
        replay_pointer = ""
        root_exhausted = mstep_exectree.Is_app_root_exhausted(app)

        while (root_exhausted != True):

            app = mstep_repo.Read_given_application(app_name)

            # TO-DO: check if execution tree is partially exhausted or not.
            # TO-DO: select appropriate coll. bp. to continue automatic debugging from
        
            instance_id = ""

            # Check if replay_pointer is empty or not.
            # If it is, then start instance and exhaust an execution path
            # If pointer is not empty, replay to that state.
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

                # Wait for consistent global state
                logger.info('Waiting for instance to reach consistent global state...')
                while (mstep_repo.Is_infra_in_consistent_global_state(instance_id) == False):
                    time.sleep(5)

                # Print current state
                logger.info('Consistent global state reached!\r\n')
                mstep_logger.List_nodes_in_infra(instance_id)

                # Check if current state already exists in exec-tree, If no, insert it
                process_states = mstep_repo.Get_global_state_for_infra(instance_id)
                app_instance = mstep_repo.Read_given_infrastructure(instance_id)

                next_coll_bp_id = mstep_exectree.Does_current_state_exist(app, app_instance, process_states)

                if (next_coll_bp_id != ""):
                    # Current state already exists in the execution tree
                    logger.info('Current state already exists ({}).'.format(next_coll_bp_id))
                else:
                    # Current state does not exist in the execution tree, insert new collective breakpoint
                    next_coll_bp_id = mstep_exectree.Create_collective_breakpoint(app, app_instance, process_states)
                    logger.info('New collective breakpoint created ({}).'.format(next_coll_bp_id))

                # Update (infrastructure) instance current collective breakpoint ID
                mstep_repo.Update_instance_current_collective_breakpoint(instance_id, next_coll_bp_id)
                app_instance = mstep_repo.Read_given_infrastructure(instance_id)

                if (app_instance.finished == 1):
                    finished = 1

            # Instance finished
            app = mstep_repo.Read_given_application(app.app_name)
            app_instance = mstep_repo.Read_given_infrastructure(instance_id)
            process_states = mstep_repo.Get_global_state_for_infra(instance_id)           
            mstep_exectree.Update_closest_alternative_coll_bp(app, app_instance.curr_coll_bp, process_states)

            # Set replay pointer to closest, non-exhausted alternative breakpoint (this can be the root itself)
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
    
    # Check if app exists
    if (mstep_repo.App_exists(app_name) == True):

        # Application exists
        app = mstep_repo.Read_given_application(app_name)

        # Start applciation/infrastructure instance
        instance_id = Start_infra_instance(app)

        if (instance_id == ""):
            logger.info('Some error has occured during application instance creation...')
            return

        # After instance reached root state, step one process each time until finished status achieved
        while (mstep_repo.Read_given_infrastructure(instance_id).finished == 0):

            # Read user input, until a valid process ID is given
            step_ok = False

            while (step_ok == False):

                process_to_step = str(input('Enter a non-finished process (VM) ID to step: '))

                if (mstep_repo.Node_exists(instance_id, process_to_step) == True and mstep_repo.Read_given_node(instance_id, process_to_step).finished == 0):
                    step_ok = True

            logger.info('Stepping process: "{} / {}"\r\n'.format(instance_id, process_to_step))

            # Step choosen process
            mstep_repo.Update_node_step_permission(instance_id, process_to_step)

            # Print current status
            mstep_logger.List_nodes_in_infra(instance_id)

            # Wait for consistent global state
            logger.info('Waiting for instance to reach consistent global state...')
            while (mstep_repo.Is_infra_in_consistent_global_state(instance_id) == False):
                time.sleep(5)
            
            # Consistent global state reached
            # Print current status
            logger.info('Consistent global state reached!\r\n')
            mstep_logger.List_nodes_in_infra(instance_id)

            # Check if current state already exists in exec-tree, If no, insert it
            process_states = mstep_repo.Get_global_state_for_infra(instance_id)
            app_instance = mstep_repo.Read_given_infrastructure(instance_id)

            next_coll_bp_id = mstep_exectree.Does_current_state_exist(app, app_instance, process_states)

            if (next_coll_bp_id != ""):
                # Current state already exists in the execution tree
                logger.info('Current state already exists ({}).'.format(next_coll_bp_id))
            else:
                # Current state does not exist in the execution tree, insert new collective breakpoint
                next_coll_bp_id = mstep_exectree.Create_collective_breakpoint(app, app_instance, process_states)
                logger.info('Current state does not exist in execution tree, new collective breakpoint created ({}).'.format(next_coll_bp_id))

                # Check for final state
                # Update closest alternative parent node to exhausted if needed

                app_instance = mstep_repo.Read_given_infrastructure(instance_id)

                if (app_instance.finished == 1):
                    app = mstep_repo.Read_given_application(app.app_name)
                    mstep_exectree.Update_closest_alternative_coll_bp(app, next_coll_bp_id, process_states)

            # Update (infrastructure) instance current collective breakpoint ID
            mstep_repo.Update_instance_current_collective_breakpoint(instance_id, next_coll_bp_id)
     
        # Exection path exhausted, destroy instance
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

    # Check if app exists
    if (mstep_repo.App_exists(app_name) == True):

        app = mstep_repo.Read_given_application(app_name)

        # Check if targeted state exists
        if (mstep_exectree.Does_coll_bp_exist(app, target_coll_bp_id) == True):

            logger.info('Given collective breakpoint exists.')

            # Start an application instance
            instance_id = Start_infra_instance(app)

            if (instance_id != ""):
                curr_process_states = json.dumps(mstep_repo.Get_global_state_for_infra(instance_id))
                target_process_states = mstep_exectree.Get_process_states_of_coll_bp(app, target_coll_bp_id)

                # Go until targeted state is not reached
                while (curr_process_states != target_process_states):

                    logger.info('Target state not reached yet...')
                    
                    app_instance = mstep_repo.Read_given_infrastructure(instance_id)

                    # Get next global state to reach
                    next_coll_bp_id = mstep_exectree.Get_next_coll_bp_id_to_target(app, app_instance.curr_coll_bp, target_coll_bp_id)
                    next_process_states = mstep_exectree.Get_process_states_of_coll_bp(app, next_coll_bp_id)

                    logger.info('Next coll. bp.: {}'.format(next_coll_bp_id))

                    print('\r\nCurrent state:\r\n{}\r\n'.format(curr_process_states))
                    print('Targeted state:\r\n{}\r\n'.format(target_process_states))
                    print('Next state:\r\n{}\r\n'.format(next_process_states))

                    # Calculate process to step
                    process_to_step = mstep_repo.Read_given_node(app_instance.infra_id, Get_proc_id_to_step(app_instance.infra_id, curr_process_states, next_process_states))

                    print('Process to step: {} ("{}")\r\n'.format(process_to_step.node_id, process_to_step.node_name))

                    # Step process
                    logger.info('Stepping process: "{} / {}"\r\n'.format(app_instance.infra_id, process_to_step.node_id))
                    Step_given_node(app_instance.infra_id, process_to_step.node_id, silent=True)

                    # Wait until consistent global state is reached
                    logger.info('Waiting for instance to reach consistent global state...')
                    while (mstep_repo.Is_infra_in_consistent_global_state(app_instance.infra_id) == False):
                        time.sleep(5)

                    # Store new coll bp id, update current global state
                    mstep_repo.Update_instance_current_collective_breakpoint(app_instance.infra_id, next_coll_bp_id)
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
                            # Read user input, until a valid process ID is given
                            step_ok = False
                            while (step_ok == False):
                                process_to_step = str(input('Enter a non-finished process (VM) ID to step: '))
                                if (mstep_repo.Node_exists(instance_id, process_to_step) == True and mstep_repo.Read_given_node(instance_id, process_to_step).finished == 0):
                                    step_ok = True
                            
                            logger.info('Stepping process: "{} / {}"\r\n'.format(instance_id, process_to_step))

                            # Step choosen process
                            mstep_repo.Update_node_step_permission(instance_id, process_to_step)

                            # Print current status
                            mstep_logger.List_nodes_in_infra(instance_id)

                            # Wait for consistent global state
                            logger.info('Waiting for instance to reach consistent global state...')
                            while (mstep_repo.Is_infra_in_consistent_global_state(instance_id) == False):
                                time.sleep(5)  

                            # Consistent global state reached
                            # Print current status
                            logger.info('Consistent global state reached!\r\n')
                            mstep_logger.List_nodes_in_infra(instance_id)

                            # Check if current state already exists in exec-tree, If no, insert it
                            process_states = mstep_repo.Get_global_state_for_infra(instance_id)
                            app_instance = mstep_repo.Read_given_infrastructure(instance_id)

                            next_coll_bp_id = mstep_exectree.Does_current_state_exist(app, app_instance, process_states)

                            if (next_coll_bp_id != ""):
                                # Current state already exists in the execution tree
                                logger.info('Current state already exists ({}).'.format(next_coll_bp_id))
                            else:
                                # Current state does not exist in the execution tree, insert new collective breakpoint
                                next_coll_bp_id = mstep_exectree.Create_collective_breakpoint(app, app_instance, process_states)
                                logger.info('Current state does not exist in execution tree, new collective breakpoint created ({}).'.format(next_coll_bp_id))

                                # Check for final state
                                # Update closest alternative parent node to exhausted if needed

                                app_instance = mstep_repo.Read_given_infrastructure(instance_id)

                                if (app_instance.finished == 1):
                                    mstep_exectree.Update_closest_alternative_coll_bp(app, next_coll_bp_id, process_states)

                            # Update (infrastructure) instance current collective breakpoint ID
                            mstep_repo.Update_instance_current_collective_breakpoint(instance_id, next_coll_bp_id)
                        
                        # Exection path exhausted, destroy instance if needed
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

    # If the number of unfinished processes is one, select that one process
    if (num_unfinished == 1):      
        for act_proc in processes:
            if act_proc.finished == 0: return act_proc.node_id
    # If not, check if any children exists for the current collective breakpoint
    else: 
        child_nodes = mstep_exectree.Get_list_of_children_nodes(app, app_instance.curr_coll_bp)

        # This is ABC
        # No children, select first non-finished process
        if (len(child_nodes) == 0):       
            for act_proc in processes:
                if act_proc.finished == 0: return act_proc.node_id
        # There are children, select next appropriate process
        else:
            traversed_states = []
            for act_child in child_nodes:
                traversed_states.append(json.loads(mstep_exectree.Get_process_states_of_coll_bp(app, act_child)))

            i = 0
            j = 0
            proc_name = processes[0].node_name
            
            # Iterate over app. instance processes
            for act_proc in processes:
                # If process is unfinished, create a test state
                if (act_proc.finished == 0):
                    test_state = json.loads(json.dumps(mstep_repo.Get_global_state_for_infra(app_instance.infra_id)))
                    test_state[act_proc.node_name][i] += 1

                    print('Curr state: {}'.format(json.loads(json.dumps(mstep_repo.Get_global_state_for_infra(app_instance.infra_id)))))
                    print('Test state: {}'.format(test_state))
                    print('Traversed states: {}'.format(traversed_states))
                    input('waiting...')

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