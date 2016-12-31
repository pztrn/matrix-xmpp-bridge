from sqlalchemy import Column, Integer, String, VARCHAR

from lib.common_libs import common
DBMap = common.TEMP_SETTINGS["DBMap"]

class Rooms(DBMap):
    __tablename__ = "rooms"

    room_id = Column("room_id", String, primary_key = True, unique = True)
    room_type = Column("room_type", Integer, nullable = False)
    commander = Column("commander", String, nullable = False)
