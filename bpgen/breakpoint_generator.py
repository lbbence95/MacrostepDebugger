# Represents the controller module of the debugger

from multiprocessing.connection import wait
from jmespath import search
import data.repository as mstep_repo
import util.logger as mstep_logger
import controller.orchestratorhandler.orch_factory as mstep_orch_factory
import logging, os.path, re, shutil

#Logger setup
logger = logging.getLogger('controller')
logger.propagate = False
logger.setLevel(logging.INFO)

breakpoint_generator = logging.StreamHandler()
formatter = logging.Formatter('*** (%(asctime)s): %(message)s', "%Y-%m-%d %H:%M:%S")
breakpoint_generator.setFormatter(formatter)

logger.addHandler(breakpoint_generator)

def Generate_breakpoints(app_name):
    """Generates breakpoints for the given application. The function searches for Cloud-init files in the application's 'context' subfolder,
    then generates breakpoint instrumented files. Creates these new files in the 'generated' subfolder. At least 2 breakpoints will be generated in the files.

    Args:
        app_name (string): An application name.
    """

    # Check if application exists
    if (mstep_repo.App_exists(app_name) == True):
        # Application exists
        app = mstep_repo.Read_given_application(app_name)

        logger.info('Application "{}" exists.'.format(app.app_name))

        # Application exists, get working directory
        main_dir = os.path.join(os.getcwd(), *(app.infra_file.split(os.sep)[0:2]))
        context_dir = os.path.join(os.getcwd(), *(app.infra_file.split(os.sep)[0:2]), "context")

        if (os.path.exists(context_dir) == True):
            context_files = [f for f in os.listdir(context_dir) if os.path.isfile(os.path.join(context_dir, f))]

            logger.info('Existing contextualization files: {}'.format(context_files))

            generated_dir = os.path.join(main_dir, "generated")

            # Check if 'generated' subfolder exists
            # TO-DO: ask for permission from the user
            if (os.path.exists(generated_dir) == True):
                logger.info('Subfolder "generated" exists. Deleting contents.')
                shutil.rmtree(generated_dir)

            os.mkdir(generated_dir)
            logger.info('Subfolder "generated" created.')

            # Iterate over contextualization files, then insert breakpoints.

            for act_context_file in context_files:

                orch_handler = mstep_orch_factory.GetOrchHandler(app.orch)

                comm_points_lines = []
                run_cmd_line = 0

                act_file = os.path.join(context_dir, act_context_file)
                generated_file = os.path.join(generated_dir, act_context_file)

                with open(act_file, "r") as f:
                    logger.info('Generating breakpoints in "{}".'.format(act_context_file))                  
                    contents = f.readlines()

                    # Start of runcmd section
                    run_cmd_line = contents.index('runcmd:\n')
                    # Communication points in runcmdsection
                    comm_points_lines = [x for x in [i for i, act_line in enumerate(contents) if re.search(orch_handler.app_regex, act_line)] if x > run_cmd_line]

                    # First breakpoint after 'jq' has been installed
                    jq_line = [x for x in [i for i, act_line in enumerate(contents) if re.search(re.compile('.*install jq.*'), act_line)] if x > run_cmd_line][0]

                    contents.insert(jq_line + 1, "- /tmp/MSTEP_BP.sh first\n")

                    if (len(comm_points_lines) != 0):
                        
                        bp_num = 2

                        for act_comm_line in comm_points_lines:

                            contents.insert(act_comm_line + bp_num, "- /tmp/MSTEP_BP.sh bp_{}\n".format(bp_num))

                            bp_num += 1
                    
                    if ("MSTEP_BP.sh" in contents[-1]):
                        contents[-1] = "- /tmp/MSTEP_BP.sh last last_bp\n"
                    else:
                        contents.append("- /tmp/MSTEP_BP.sh last last_bp\n")
                    
                    with open(generated_file, "w") as f:
                        contents = "".join(contents)
                        f.write(contents)

        else:
            logger.warning('Directory "context" for application "{}" does not exist.'.format(app.app_name))
    else:
        logger.info('Application "{}" does not exist.'.format(app_name))