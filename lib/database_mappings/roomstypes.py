from sqlalchemy import Column, Integer, String, VARCHAR

from lib.common_libs import common
DBMap = common.TEMP_SETTINGS["DBMap"]

class Roomstypes(DBMap):
    __tablename__ = "rooms_types"

    id = Column("id", Integer, primary_key = True, unique = True, autoincrement = True)
    name = Column("name", String(255), nullable = False)
    description = Column("description", String(255), nullable = False)
