# Represents the main file of the debugger

import src.api.rest as msteprest

if __name__ == "__main__":
    """Sets Flask configuration.
    """

    msteprest.app.run(host = '0.0.0.0', port=5000, debug = True, threaded=True)