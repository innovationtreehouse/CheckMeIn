import sqlite3
import os
from collections import namedtuple
import datetime
from enum import IntEnum


Guest = namedtuple('Guest', ['guest_id', 'displayName'])


class Status(IntEnum):
    inactive = 0
    active = 1


class Guests(object):
    def __init__(self):
        self.date = 0
        self.num = 1

    def migrate(self, dbConnection, db_schema_version):
        if db_schema_version <= 2:
            dbConnection.execute('''CREATE TABLE guests
                                (guest_id TEXT UNIQUE,
                                 displayName TEXT,
                                 email TEXT,
                                 firstName TEXT,
                                 lastName TEXT,
                                 whereFound TEXT,
                                 status INTEGER default 1
                                 )''')
        if db_schema_version <= 5:
            dbConnection.execute(
                "ALTER TABLE guests ADD COLUMN newsletter INTEGER default 0")

    def add(self, dbConnection, displayName, first, last, email, whereFound, newsletter):
        if self.date != datetime.date.today():
            self.date = datetime.date.today()
            self.num = 1
        else:
            self.num = self.num + 1

        while self.num < 10000:
            try:
                guest_id = self.date.strftime(
                    "%Y%m%d") + '{0:04d}'.format(self.num)
                # zero padded up to 9999 for each day
                dbConnection.execute("INSERT INTO guests VALUES (?,?,?,?,?,?,?,?)",
                                     (guest_id, displayName, email, first,
                                      last, whereFound, Status.active, newsletter))
            except sqlite3.DatabaseError:
                self.num = self.num + 1
            else:
                return guest_id

    def getName(self, dbConnection, guest_id):
        data = dbConnection.execute(
            "SELECT displayName FROM guests WHERE guest_id==?", (guest_id,)).fetchone()
        if data is None:
            return ('Invalid: ' + guest_id, None)
        else:
            # Add code here for inactive
            return ('', data[0])

    def getList(self, dbConnection):
        guestList = []

        for row in dbConnection.execute("SELECT * FROM guests WHERE status is NOT ? ORDER BY displayName",
                                        (Status.inactive,)):
            guestList.append(Guest(row[0], row[1]))
        return guestList



# unit test
if __name__ == "__main__":  # pragma no cover
    DB_STRING = 'data/test.db'
    try:
        os.remove(DB_STRING)   # Start with a new one
    except IOError:
        pass  # Don't care if it didn't exist
    guests = Guests()

    dbConnection = sqlite3.connect(
        DB_STRING, detect_types=sqlite3.PARSE_DECLTYPES)
    guests.migrate(dbConnection, 0)

    guests.add(dbConnection, "Test 1", "Test", "1",
               "noemail@domain.com", "", False)
    guests.add(dbConnection, "Test 2", "Test",
               "2", "noemail@domain.com", "", True)
    guests.add(dbConnection, "Test 3", "Test", "3",
               "noemail@domain.com", "", False)

    for g in guests.getList(dbConnection):
        print(g)
