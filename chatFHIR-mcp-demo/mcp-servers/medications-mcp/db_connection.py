from sqlalchemy import create_engine

def instantiate_create_engine():
    """
    Creates a SQLAlchemy engine for connecting to the InterSystems IRIS instance.
    """
    username = "SuperUser"
    password = "SYS"
    hostname = "iris"
    port = 1972
    namespace = "CHATFHIR"
    CONNECTION_STRING = f"iris://{username}:{password}@{hostname}:{port}/{namespace}"
    engine = create_engine(CONNECTION_STRING)
    return engine
