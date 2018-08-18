import cherrypy
from mako.lookup import TemplateLookup
import argparse
from visits import Visits
import datetime

DB_STRING = 'data/checkMeIn.db'
KEYHOLDER_BARCODE = '999901'

class CheckMeIn(object):
   def __init__(self):
      self.lookup = TemplateLookup(directories=['HTMLTemplates'],default_filters=['h'])
      self.visits =  Visits(DB_STRING, 'data/members.csv', 'TFI Barcode', 'TFI Display Name');

   def template(self, name, **kwargs):
      return self.lookup.get_template(name).render(**kwargs);

   def showGuestPage(self, message=''):
       all_guests = set(self.visits.guests.getList());
       building_guests = set(self.visits.reports.guestsInBuilding());

       guests_not_here = all_guests - building_guests;

       return self.template('guests.html', welcome=message,
                                           inBuilding=building_guests,
                                           guestList=guests_not_here)

   @cherrypy.expose
   def station(self,error=''):
      self.visits.checkBuilding();
      return self.template('station.html',
                           todaysTransactions=self.visits.reports.transactionsToday(),
                           numberPresent=self.visits.reports.numberPresent(),
                           uniqueVisitorsToday=self.visits.reports.uniqueVisitorsToday(),
                           keyholder_name=self.visits.getKeyholderName(),
                           error=error)

   @cherrypy.expose
   def who_is_here(self):
      return self.template('who_is_here.html',now=datetime.datetime.now(), whoIsHere=self.visits.reports.whoIsHere())

   @cherrypy.expose
   def keyholder(self, barcode):
      error = ''
      barcode = barcode.strip();
      if barcode == KEYHOLDER_BARCODE:
          self.visits.emptyBuilding();
      else:
          error = self.visits.setActiveKeyholder(barcode);
          if error:
              return self.template('keyholder.html', error=error);
          self.visits.addIfNotHere(self.keyholder_barcode)
      return self.station();

   @cherrypy.expose
   # later change this to be more ajaxy, but for now...
   def scanned(self, barcode):
      error = ''
# strip whitespace before or after barcode digits (occasionally a space comes before or after
      barcode = barcode.strip();
      if (barcode == KEYHOLDER_BARCODE) or (barcode == self.keyholder_barcode):
         return self.template('keyholder.html', whoIsHere=self.visits.reports.whoIsHere());
      else:
         error = self.visits.scannedMember(barcode);
      return self.station(error);

   @cherrypy.expose
   def admin(self,error=""):
      firstDate = self.visits.reports.getEarliestDate().isoformat()
      todayDate = datetime.date.today().isoformat()
      forgotDates = []
      for date in self.visits.reports.getForgottenDates():
          forgotDates.append(date.isoformat())
      return self.template('admin.html',forgotDates=forgotDates,
                            firstDate=firstDate,todayDate=todayDate,
                            error=error );

   @cherrypy.expose
   def reports(self, startDate, endDate):
      return self.template('reports.html', stats=self.visits.reports.getStats(startDate, endDate));

   @cherrypy.expose
   def customSQLReport(self, sql):
       data = self.visits.reports.customSQL(sql);
       return self.template('customSQL.html', sql=sql, data=data)

   @cherrypy.expose
   def addMember(self, display, barcode):
       error = self.visits.members.add(display, barcode);
       return self.admin(error);

   @cherrypy.expose
   def addGuest(self, first, last, email, hear):
       displayName = first + ' ' + last[0] + '.'
       guest_id = self.visits.guests.add(displayName, first, last, email, hear);
       self.visits.enterGuest(guest_id);
       return self.showGuestPage('Welcome ' + displayName + '  We are glad you are here!')

   @cherrypy.expose
   def fixData(self, date):
       data = self.visits.reports.getData(date);
       return self.template('fixData.html', date=date,data=data)

   @cherrypy.expose
   def fixed(self, output):
       self.visits.fix(output);
       return self.admin();

   @cherrypy.expose
   def guests(self):
       return self.showGuestPage('')

   @cherrypy.expose
   def leaveGuest(self,guest_id):
       self.visits.leaveGuest(guest_id);
       (error,name) = self.visits.guests.getName(guest_id);
       if error:
          return showGuestPage(error);

       return self.showGuestPage('Goodbye ' + name + ' We hope to see you again soon!')

   @cherrypy.expose
   def returnGuest(self,guest_id):
       self.visits.enterGuest(guest_id);
       (error,name) = self.visits.guests.getName(guest_id);
       if error:
           return showGuestPage(error);

       return self.showGuestPage('Welcome back, ' + name + ' We are glad you are here!' )

   @cherrypy.expose
   def index(self):
      return self.who_is_here();

if __name__ == '__main__':
   parser = argparse.ArgumentParser(description="CheckMeIn - building check in and out system")
   parser.add_argument('conf')
   args = parser.parse_args()

   cherrypy.quickstart(CheckMeIn(),'',args.conf)
