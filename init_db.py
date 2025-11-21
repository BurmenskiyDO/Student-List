from db import sync_engine
from models import Base


Base.metadata.create_all(sync_engine)

