from db import get_sync_engine
from models import Base


Base.metadata.create_all(get_sync_engine())

