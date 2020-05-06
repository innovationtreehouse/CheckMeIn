import cherrypy
from webBase import WebBase

class WebReports(WebBase):
    @cherrypy.expose
    def reports(self, startDate, endDate):
        return self.template('reports.mako', stats=self.engine.reports.getStats(self.dbConnect(), startDate, endDate))
    @cherrypy.expose
    def reportGraph(self, startDate, endDate):
        cherrypy.response.headers['Content-Type'] = "image/png"
        stats = self.engine.reports.getStats(
            self.dbConnect(), startDate, endDate)
        return stats.getBuildingUsageGraph()

    @cherrypy.expose
    def saveReport(self, sql, report_name):
        error = self.engine.customReports.saveCustomSQL(
            self.dbConnect(), sql, report_name)
        return self.admin(error)

    @cherrypy.expose
    def savedReport(self, report_id, error=''):
        title = "Error"
        sql = ""
        try:
            (title, sql, data) = self.engine.customReports.customReport(report_id)
        except sqlite3.OperationalError as e:
            data = repr(e)

        return self.template('customSQL.mako', report_title=title, sql=sql, data=data)

    @cherrypy.expose
    def customSQLReport(self, sql):
        try:
            data = self.engine.customReports.customSQL(sql)
        except sqlite3.OperationalError as e:
            data = repr(e)

        return self.template('customSQL.mako', sql=sql, data=data)
