import csv
import datetime
import sqlite3
import os
from collections import defaultdict
from dateutil import parser
from members import Members
from guests import Guests
from reports import Reports
from keyholders import Keyholders

SCHEMA_VERSION = 4;

class Visits(object):
  def createDB(self, filename, barcode, display):
     self.members.loadFromCSV(filename, barcode, display);
     self.guests.createTable();

     with sqlite3.connect(self.database) as c:
        c.execute('''CREATE TABLE visits
                     (start timestamp, leave timestamp, barcode text, status text)''')
        c.execute('PRAGMA schema_version = ?', (SCHEMA_VERSION,));

  def __init__(self, database, filename, barcode, display):
     self.database = database;
     self.members = Members(self.database);
     self.guests = Guests(self.database);
     self.keyholders = Keyholders(self.database);
     self.reports = Reports(self.database);
     if not os.path.exists(self.database):
          self.createDB(filename, barcode, display);
     else:
          with sqlite3.connect(self.database) as c:
             data = c.execute('PRAGMA schema_version').fetchone();
             if data[0] != SCHEMA_VERSION:
                self.migrate(c, data[0]);

  def migrate(self, dbConnection, db_schema_version):
      if db_schema_version == 1 or db_schema_version == 2 or db_schema_version == 3:
          # No change for Visits
          self.members.migrate(dbConnection, db_schema_version);
          self.guests.migrate(dbConnection, db_schema_version);
          self.keyholders.migrate(dbConnection, db_schema_version);
          dbConnection.execute('PRAGMA schema_version = ' + str(SCHEMA_VERSION));
      else:
          raise Exception("Unknown DB schema version" + str(db_schema_version) + ": " + self.database)

  def enterGuest(self, guest_id):
     now = datetime.datetime.now();
     with sqlite3.connect(self.database) as c:
        data = c.execute("SELECT * FROM visits WHERE (barcode==?) and (status=='In')", (guest_id,)).fetchone();
        if data is None:
            c.execute("INSERT INTO visits VALUES (?,?,?,'In')", (now, now, guest_id));

  def leaveGuest(self, guest_id):
     now = datetime.datetime.now();
     with sqlite3.connect(self.database) as c:
         c.execute("UPDATE visits SET leave = ?, status = 'Out' WHERE (barcode==?) AND (status=='In')",(now, guest_id))

  def scannedMember(self, barcode):
     now = datetime.datetime.now();
     with sqlite3.connect(self.database) as c:
         # See if it is a valid input
        data = c.execute("SELECT displayName FROM members WHERE barcode==?", (barcode,)).fetchone();
        if data is None:
           return 'Invalid barcode: ' + barcode;
        name = data[0];
        data = c.execute("SELECT * FROM visits WHERE (barcode==?) and (status=='In')", (barcode,)).fetchone();
        if data is None:
           c.execute("INSERT INTO visits VALUES (?,?,?,'In')", (now, now, barcode));
        else:
           c.execute("UPDATE visits SET leave = ?, status = 'Out' WHERE (barcode==?) AND (status=='In')",(now, barcode))
        return '';

  def checkBuilding(self):
    now = datetime.datetime.now()
    if now.hour == 3 and self.reports.numberPresent() > 0:  # If between 3am and 4am
       self.emptyBuilding();

  def emptyBuilding(self):
     now = datetime.datetime.now()
     keyholder_barcode = self.keyholders.getActiveKeyholder()
     with sqlite3.connect(self.database) as c:
        c.execute("UPDATE visits SET leave = ?, status = 'Forgot' WHERE status=='In'", (now,))
        if keyholder_barcode:
           c.execute("UPDATE visits SET status = 'Out' WHERE barcode==? AND leave==?", (keyholder_barcode, now))
     if keyholder_barcode:
        self.keyholders.setActiveKeyholder('')

  def oopsForgot(self):
    now = datetime.datetime.now()
    startDate = now.replace(hour=0,minute=0,second=0,microsecond=0);
    with sqlite3.connect(self.database) as c:
       c.execute("UPDATE visits SET status = 'In' WHERE status=='Forgot' AND leave > ?", (startDate,))

  def uniqueVisitors(self, startDate, endDate):
     with sqlite3.connect(self.database) as c:
        numUniqueVisitors = c.execute("SELECT COUNT(DISTINCT barcode) FROM visits WHERE (start BETWEEN ? AND ?)", (startDate, endDate)).fetchone()[0]

  def getKeyholderName(self):
      barcode = self.keyholders.getActiveKeyholder();
      if barcode:
          (error, display) = self.members.getName(barcode)
          return display
      else:
          return 'N/A'

  def setActiveKeyholder(self, barcode):
      #TODO: once keyholders does verification, this should have the possibility of error
      self.keyholders.setActiveKeyholder(barcode);
      self.addIfNotHere(barcode)
      return ''

  def addIfNotHere(self, barcode):
     now = datetime.datetime.now()
     with sqlite3.connect(self.database) as c:
         c.execute('''INSERT INTO visits (START,LEAVE,BARCODE,STATUS)
                      SELECT ?,?,?,'In'
                      WHERE NOT EXISTS(
                          SELECT 1 FROM visits
                          WHERE ((barcode==?) and (status=='In')))''',
                   (now, now, barcode, barcode));
  def fix(self, fixData):
    entries = fixData.split(',')

    with sqlite3.connect(self.database,detect_types=sqlite3.PARSE_DECLTYPES) as c:
       for entry in entries:
           tokens = entry.split('!')
           if len(tokens) == 3:
               rowID = tokens[0];
               newStart = parser.parse(tokens[1]);
               newLeave = parser.parse(tokens[2]);

               # if crossed over midnight....
               if(newLeave < newStart):
                  newLeave += datetime.timedelta(days=1)

               c.execute('''UPDATE visits SET start = ?, leave = ?, status = 'Out'
                            WHERE (visits.rowid==?)''',(newStart, newLeave, rowID))
# unit test
def testOutput(testNum, test):
  result = test;
  if result:
      print("Result: ", result)
  print(testNum, visits.reports.whoIsHere());

if __name__ == "__main__":
    DB_STRING = 'data/test.db'
    try:
       os.remove(DB_STRING);   # Start with a new one
    except:
       pass; # Don't care if it didn't exist

    visits = Visits(DB_STRING, 'data/members.csv', 'TFI Barcode', 'TFI Display Name');
    testOutput(1, '');
    testOutput(2, visits.scannedMember('100091'));
    testOutput(3, visits.scannedMember('100090'));
    testOutput(4, visits.scannedMember('100090'));
    guest_id = visits.guests.add('Guest 1');
    testOutput(5, visits.enterGuest(guest_id));
    testOutput(6, visits.leaveGuest(guest_id));
    testOutput(7, visits.scannedMember('100091'));
    testOutput(8, visits.addIfNotHere('100091'));
    testOutput(9, visits.addIfNotHere('100091'));
    testOutput(10, visits.emptyBuilding('100091'));
# TODO: Add test for fix
