Bence Ligetfalvi & SZTAKI

Basic macrostep based debugger with an API and CLI.

Main file: src\debugger.py

Usage: src\debugger.py [options]. Current directory should be the main folder.

Optional arguments:
  -h, --help            show this help message and exit
  -li, --infrastructures
                        list managed infrastructures
  -ln, --nodes          list managed nodes
  -s, --start           start the macrostep debugger service (can be used with -p)
  -p , --port           macrostep debugger service port (default is 5000)
  -dn , --detailsnode   show details of the given node (Important! Used after option -di, cannot be used on its own)
  -di , --detailsinfra
                        show details of the given infrastructure.
  -i , --infra          permit a node in the given infrastructure to move to the next breakpoint
  -n , --node           a node ID (Important! Used after option -i, cannot be used on its own)