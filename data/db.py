# Represents the database layer of the application

import logging, sqlite3, sqlalchemy
from sqlalchemy import create_engine, Column, Integer, ForeignKey, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.sql.expression import update

#Logger setup
logger = logging.getLogger('db')
logger.propagate = False
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
formatter = logging.Formatter('*** (%(asctime)s): %(message)s', "%Y-%m-%d %H:%M:%S")
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)


# sqlite
db_conn = sqlite3.connect('data/mstepDB.db')

# SQLalchemy
Base = declarative_base()
engine = create_engine('sqlite:///data/mstepDB.db', echo=False)
Base.metadata.create_all(bind=engine)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

#Models
#Application
class Application(Base):
    __tablename__ = "Applications"
    app_name = Column("app_name", Text, primary_key=True, nullable=False)
    creation_date = Column("cr_date", DateTime, nullable=False)
    infra_file = Column("infra_file", Text, nullable=False)
    processes = Column('processes', Text, nullable=False, default="")
    orch = Column("orch", Text, nullable=False)
    orch_loc = Column("orch_loc", Text, nullable=False)
    curr_coll_bp = Column('curr_coll_bp', Text, nullable=False, default="")
    root_coll_bp = Column('root_coll_bp', Text, nullable=False, default="")

    infra_instances = relationship("Infrastructure")

#Infrastructure
class Infrastructure(Base):
    __tablename__ = "Infrastructures"
    app_name = Column("app_name", Text, ForeignKey("Applications.app_name"), primary_key=True)
    infra_id = Column("infra_id", Text, primary_key=True, nullable=False)
    infra_name = Column("infra_name", Text, default="", nullable=False)
    registration_date = Column("registered", DateTime)
    finished = Column("finished", Integer, default=0)
    curr_coll_bp = Column('curr_coll_bp', Text, nullable=False, default="")
    is_freerun = Column('is_freerun', Integer, default=0)

    nodes = relationship("Node")

#Node
class Node(Base):
    __tablename__ = "Nodes"
    infra_id = Column("infra_id", Text, ForeignKey("Infrastructures.infra_id"), primary_key=True)
    node_id = Column("node_id", Text, nullable=False, primary_key=True)
    node_name = Column("node_name", Text)
    registered = Column("registered", DateTime)
    curr_bp = Column("curr_bp", Integer, default=0)
    move_next = Column("move_next", Integer, default=0)
    public_ip = Column("public_ip", Text, default="")
    finished = Column("finished", Integer, default=0)
    bp_up_to_date = Column("bp_up_to_date", Integer, default=0)
    refreshed = Column("refreshed", Integer, default=0)

    breakpoints = relationship("Breakpoint")

#Breakpoint
class Breakpoint(Base):
    __tablename__ = "Breakpoints"
    infra_id = Column("infra_id", Text, ForeignKey("Infrastructures.infra_id"), primary_key=True)
    node_id = Column("node_id", Text, ForeignKey("Nodes.node_id"), primary_key=True)
    bp_reg = Column("bp_reg", DateTime)
    bp_num = Column("bp_num", Integer, primary_key=True)
    bp_data = Column("bp_data", Text)
    bp_tag = Column("bp_tag", Text, default="")


#Functions, methods
# Initialization
def Initialize_db():
    """Drops tables and initializes a new database file.
    """

    curr = db_conn.cursor()

    # Application
    curr.execute("""DROP TABLE IF EXISTS Applications""")
    curr.execute("""CREATE TABLE Applications (
        app_name TEXT NOT NULL PRIMARY KEY,
        cr_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        infra_file TEXT NOT NULL,
        processes TEXT NOT NULL DEFAULT "",
        orch TEXT NOT NULL,
        orch_loc TEXT NOT NULL,
        curr_coll_bp TEXT NOT NULL DEFAULT "",
        root_coll_bp TEXT NOT NULL DEFAULT ""
    )""")

    # Infrastructures
    # An infrastructure instance is identified its: infrastructure ID (infraID). Also important data is the infrastucture name (infraName).
    # The time when it was registered is also stored (registered).
    curr.execute("""DROP TABLE IF EXISTS Infrastructures""")
    curr.execute("""CREATE TABLE Infrastructures (
        app_name TEXT NOT NULL,
        infra_id TEXT NOT NULL PRIMARY KEY,
        infra_name TEXT NOT NULL DEFAULT "",
        registered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        finished INTEGER DEFAULT 0,
        curr_coll_bp TEXT NOT NULL DEFAULT "",
        is_freerun INTEGER DEFAULT 0,
        FOREIGN KEY (app_name) REFERENCES Application (app_name)
    ) """)

    # Nodes
    # Nodes currently represent virtual machines (VM).
    curr.execute("""DROP TABLE IF EXISTS Nodes""")
    curr.execute("""CREATE TABLE Nodes (
        infra_id TEXT NOT NULL,
        node_id TEXT NOT NULL,
        node_name TEXT,
        registered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        curr_bp INTEGER DEFAULT 0,
        move_next INTEGER DEFAULT 0,
        public_ip TEXT DEFAULT "",
        finished INTEGER DEFAULT 0,
        bp_up_to_date INTEGER DEFAULT 0,
        refreshed INTEGER DEFAULT 0,
        PRIMARY KEY (infra_id, node_id),
        FOREIGN KEY (infra_id) REFERENCES Infrastructure (infra_id)
    ) """)

    # Breakpoints
    curr.execute("""DROP TABLE IF EXISTS Breakpoints""")
    curr.execute("""CREATE TABLE Breakpoints (
        infra_id TEXT NOT NULL,
        node_id TEXT NOT NULL,
        bp_reg TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        bp_num INTEGER,
        bp_data TEXT,
        bp_tag TEXT DEFAULT "",
        PRIMARY KEY (infra_id, node_id, bp_num),
        FOREIGN KEY (infra_id) REFERENCES Infrastructure (infra_id),
        FOREIGN KEY (node_id) REFERENCES Nodes (node_id)
    )""")

    # # Tracking table
    # curr.execute("""DROP TABLE IF EXISTS Tracking""")
    # curr.execute("""CREATE TABLE Tracking (
    #     app_name TEXT NOT NULL,
    #     infraID TEXT NOT NULL,
    #     curr_coll_BP_ID TEXT NOT NULL,
    #     PRIMARY KEY (app_name, infraID),
    #     FOREIGN KEY (infraID) REFERENCES Infrastructure (infraID)
    # )""")

    db_conn.commit()
    db_conn.close()

# Create
# Create application
def Register_application(new_application):
    """Creates a new application database entry.

    Args:
        new_application (Application): An application.
    """

    sql_session = Session()  

    try:
        sql_session.add(new_application)
        sql_session.commit()
        logger.info('New application "{}" ({}) registered!'.format(new_application.app_name, new_application.orch.upper()))
    except sqlalchemy.exc.IntegrityError:
        logger.info('Application "{}" ({}) already registered!'.format(new_application.app_name, new_application.orch.upper()))
    
    Session.remove()

# Create infrastructure
def Register_infrastructure(new_infra):
    """Creates a new infrastructure database entry.

    Args:
        new_infra (Infrastructure): An infrastructure.
    """

    sql_session = Session()  

    try:
        sql_session.add(new_infra)
        sql_session.commit()
        logger.info('New infrastructure "{}" ("{}") registered!'.format(new_infra.infra_id, new_infra.infra_name))
    except sqlalchemy.exc.IntegrityError:
        logger.info('Infrastructure "{}" already registered"'.format(new_infra.infra_id))
    
    Session.remove()

# Create node
def Register_node(new_node):
    """Creates a new node database entry.

    Args:
        new_node (Node): A node.
    """

    sql_session = Session()   

    try:
        sql_session.add(new_node)
        sql_session.commit()
        logger.info('New node "{}/{}" registered!'.format(new_node.infra_id, new_node.node_id))
    except sqlalchemy.exc.IntegrityError:
        logger.info('Node "{}/{}" already registered!'.format(new_node.infra_id, new_node.node_id))
    
    Session.remove()

# Create breakpoint
def Register_breakpoint(new_bp):
    """Creates a new breakpoint database entry.

    Args:
        new_bp (Breakpoint): A breakpoint.
    """

    sql_session = Session()
    
    try:
        sql_session.add(new_bp)
        sql_session.commit()
        logger.info('New breakpoint (#{}) for node "{}/{}" registered!'.format(new_bp.bp_num, new_bp.infra_id, new_bp.node_id))
    except sqlalchemy.exc.IntegrityError:
        logger.info('Breakpoint #{} for node "{}/{}" already registered!'.format(new_bp.bp_num, new_bp.infra_id, new_bp.node_id))
    
    Session.remove()


# Read all application
def Read_all_application():
    """Reads all applications.

    Returns:
        list: A list of Applications.
    """

    sql_session = Session()
    data = sql_session.query(Application).all()
    Session.remove()
    return data

# Read all infrastructure
def Read_all_infrastructure():
    """Reads all infrastructures.

    Returns:
        list: A list of Infrastructures.
    """

    sql_session = Session()
    
    data = sql_session.query(Infrastructure).all()
    Session.remove()
    return data

# Read all node
def Read_all_node():
    """Reads all nodes.

    Returns:
        list: A list of Nodes.
    """

    sql_session = Session()
    
    data = sql_session.query(Node).all()
    Session.remove()
    return data

# Read all breakpoint
def Read_all_breakpoint():
    """Reads all breakpoints.

    Returns:
        list: A list of Breakpoints.
    """

    sql_session = Session()
    
    data = sql_session.query(Breakpoint).all()
    Session.remove()
    return data

# Update
# Update application root collective breakpoint
def Update_app_root_collective_breakpoint(app_name, root_id):
    """Updates an application's root collective breakpoint.

    Args:
        app_name (string): An application name.
        root_id (string): UUID of the new root.
    """

    sql_session = Session()
    
    sql_session.query(Application).filter(Application.app_name == app_name).update({'root_coll_bp':root_id})
    sql_session.commit()
    Session.remove()

# Update application current collective breakpoint
def Update_app_current_collective_breakpoint(app_name, coll_bp_id):
    """Updates an application's current collective breakpoint.

    Args:
        app_name (string): An application name.
        coll_bp_id (string): A collective breakpoint ID.
    """

    sql_session = Session()
    
    sql_session.query(Application).filter(Application.app_name == app_name).update({'curr_coll_bp':coll_bp_id})
    sql_session.commit()
    Session.remove()

# Update infrastructure name
def Update_infrastructure_name(infra_id, new_infra_name):
    """Updates an infrastructure's name.

    Args:
        infra_id (string): An infrastructure ID.
        new_infra_name (string): An infastructure name.
    """

    sql_session = Session()
    
    sql_session.query(Infrastructure).filter(Infrastructure.infra_id == infra_id).update({'infra_name':new_infra_name})
    sql_session.commit()
    Session.remove()

def Update_instance_current_collective_breakpoint(infra_id, coll_bp_id):
    """Updates the given infrastructure's current collective breakpoint to the given collective breakpoint ID.

    Args:
        infra_id (string): An infrastructure ID.
        coll_bp_id (string): A collective breakpoint ID.
    """

    sql_session = Session()
    
    sql_session.query(Infrastructure).filter(Infrastructure.infra_id == infra_id).update({'curr_coll_bp':coll_bp_id})
    sql_session.commit()
    Session.remove()


def Update_node_permission(infra_id, node_id):
    """Updates a given node's step permission.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): An node ID.
    """

    sql_session = Session()
    
    sql_session.query(Node).filter(Node.infra_id == infra_id, Node.node_id == node_id).update({'move_next':1})
    sql_session.commit()
    Session.remove()

def Update_node_current_bp_and_permission(infra_id, node_id):
    """Updates a given nodes current breakpoint and it's permission.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): An node ID.
    """

    sql_session = Session()
    
    sql_session.query(Node).filter(Node.infra_id == infra_id, Node.node_id == node_id).update({'move_next':0, 'curr_bp': Node.curr_bp + 1})
    sql_session.commit()
    Session.remove()

def Update_node_status_finished(infra_id, node_id):
    """Updates the given node's status as finished, meaning the node has reached its last breakpoint.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A node ID.
    """

    sql_session = Session()
    
    sql_session.query(Node).filter(Node.infra_id == infra_id, Node.node_id == node_id).update({'finished':1})
    sql_session.commit()
    Session.remove()

    # Check if infrastucture instance has finished
    Update_infra_status_finished(infra_id)

def Update_infra_status_finished(infra_id):
    """Updates a given infrastructure's status as finished, meaning every node has finished.

    Args:
        infra_id (string): An infrastructure ID.
    """

    sql_session = Session()
    
    nodes = list(sql_session.query(Node).filter(Node.infra_id == infra_id, Node.finished == 0))
    
    if (len(nodes) == 0):
        sql_session.query(Infrastructure).filter(Infrastructure.infra_id == infra_id).update({'finished':1})
        sql_session.commit()

    Session.remove()

def Update_proc_to_refreshed_in_infra(infra_id, node_id, false_true_int):
    """Updates the refreshed field of all process in infrastructure to the described value.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): A process ID.
        false_true_int: 0 for False, 1 for True.
    """

    sql_session = Session()

    sql_session.query(Node).filter(Node.infra_id == infra_id, Node.node_id == node_id).update({'refreshed':false_true_int})
    sql_session.commit()

    Session.remove()

def Update_process_breakpoint_info(infra_id, node_id, data):
    """Updates a process's current breakpoint information.

    Args:
        infra_id (string): An infrastructure ID.
        node_id (string): An node/process ID.
        data (string): The received breakpoint informations in JSON.
    """

    sql_session = Session()

    curr_bp = list(filter(lambda x: x.infra_id == infra_id and x.node_id == node_id, Read_all_node()))[0].curr_bp

    sql_session.query(Breakpoint).filter(Breakpoint.infra_id == infra_id, Breakpoint.node_id == node_id, Breakpoint.bp_num == curr_bp).update({'bp_data': data})
    sql_session.commit()

    Session.remove()