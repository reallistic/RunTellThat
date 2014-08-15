import sqlite3, os, time, urllib
from logger import logger

class ApiLogger:
    db = None
    logfile = "apilogger.db"
    activated = True
    uriid = None
    filewascreated = 2

    def __init__(self,dbfile = None):
        self.filewascreated = 2
        if dbfile:
            self.logfile = dbfile
        else:
            self.logfile = 'apilogger.db'
        if not os.path.isfile(self.logfile):
            logger.debug("Creating db")
            self.create_db()
        else:
            logger.debug("Loading db")
            self.db = sqlite3.connect(self.logfile)
            self.db.close()
            self.create_db()
            self.filewascreated = 1
            self.activated = True

    def create_db(self):
        self.db = sqlite3.connect(self.logfile, detect_types=sqlite3.PARSE_DECLTYPES)
        c = self.db.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS uri
          (id INTEGER PRIMARY KEY, request_uri STRING, method TEXT, full_uri TEXT,
          UNIQUE (request_uri,method) ON CONFLICT IGNORE)''')

        c.execute('''CREATE TABLE IF NOT EXISTS query_string
          (id INTEGER PRIMARY KEY, title TEXT, request INTEGER,
          UNIQUE (title, request) ON CONFLICT IGNORE)''')

        c.execute('''CREATE TABLE IF NOT EXISTS data
          (id INTEGER PRIMARY KEY, data_text TEXT, request INTEGER, response INTEGER,
          UNIQUE (data_text, request, response) ON CONFLICT IGNORE)''')

        c.execute('''CREATE TABLE IF NOT EXISTS headers
          (id INTEGER PRIMARY KEY, name TEXT, request INTEGER, response INTEGER,
          UNIQUE (name, request,response) ON CONFLICT IGNORE)''')
        self.db.commit()
        self.db.close()

    def save_headers(self, headers, response = 0):
        for value in headers.keys():
            self.db_op("INSERT INTO headers (name, request, response) VALUES(?, ?, ?)", (value, self.uriid,response))

    def save_data(self, data, response = 0):
        self.db_op("INSERT INTO data (data_text, request, response) VALUES(?, ?, ?)", (data, self.uriid, response))

    def save_uriparts(self, uri, method, query_string):
        full_uri = uri
        if len(query_string) >0:
            logger.debug("query_string is %s" % query_string)
            try:
                full_uri = "%s?%s" % (uri, urllib.urlencode(query_string))
            except:
                full_uri = uri
                logger.error("Error getting full uri from urlencode %s" % query_string)
        uriid = self.db_op("INSERT INTO uri (request_uri,method,full_uri) VALUES (?, ?, ?)", (uri,method,full_uri))
        if not uriid:
            uriid = self.db_querySingle("SELECT id FROM uri WHERE request_uri = ? AND method = ?", (uri, method))
            uriid = uriid[0]
        if not uriid:
            logger.error("Error getting id of uri")
            self.activated=False
            return

        self.uriid = uriid
        if len(query_string) >0:
            for kvp in query_string.keys():
                self.db_op("INSERT INTO query_string (title, request) VALUES(?,?)",(kvp, uriid))

    def LOG(self, request, response):
        if not self.activated:
            return
        if "/web/" in request.path:
            return
        self.save_uriparts(request.path,request.method, request.query)
        if not self.activated:
            return
        self.save_headers(request.headers)
        self.save_headers(response.headers, 1)
        if "content-Type" in response.headers.keys() and "/xml" in response.headers["Content-Type"]:
           self.save_data(response.body, 1)

    def db_op(self, sql, param, tried =0):
        self.db = sqlite3.connect(self.logfile, detect_types=sqlite3.PARSE_DECLTYPES)
        c = self.db.cursor()
        lasterror = 0
        result = None
        try:
            c.execute(sql,param)
            result = c.lastrowid        
        except sqlite3.Error as e:
            logger.error("[db_op] %s Error running sqlite3 query %s" % (sql, e.args[0]))
        self.db.commit()
        self.db.close()
        if tried <3 and lasterror == 5:
            randn = rand ( 1 , 5 )
            logger.error("SQLITE DB Locked. Sleeping for randn seconds")
            time.sleep(randn)
            self.db_op(sql, param, (tried+1))
        elif tried >=3 and lasterror == 5:
            return None        
        else:
            return result

    def db_query(self, sql, param = None, tried =0):
        self.db = sqlite3.connect(self.logfile, detect_types=sqlite3.PARSE_DECLTYPES)
        c = self.db.cursor()
        rows = None
        lasterror = 0
        try:
            if param:
                c.execute(sql, param)
            else:
                c.execute(sql)
            rows = c.fetchall()        
        except sqlite3.Error as e:
            logger.error("[db_query] %s Error running sqlite3 query %s" % (sql, e.args[0]))
        self.db.close()
        if tried <3 and lasterror == 5:
            randn = rand ( 1 , 5 )
            logger.error("SQLITE DB Locked. Sleeping for randn seconds")
            time.sleep(randn)
            self.db_query(sql,param, (tried+1))
        elif tried >=3 and lasterror == 5:
            return None
        else:
            return rows

    def db_querySingle(self, sql, param, tried =0):
        self.db = sqlite3.connect(self.logfile, detect_types=sqlite3.PARSE_DECLTYPES)
        c = self.db.cursor()
        rows = None
        lasterror = 0
        try:
            result = c.execute(sql, param)
            rows = c.fetchone()        
        except sqlite3.Error as e:
            logger.error("[db_querySingle] %s Error running sqlite3 query %s" % (sql, e.args[0]))
        self.db.close()
        if tried <3 and lasterror == 5:
            randn = rand ( 1 , 5 )
            logger.error("SQLITE DB Locked. Sleeping for randn seconds")
            time.sleep(randn)
            self.db_querySingle(sql,param, (tried+1))
        elif tried >=3 and lasterror == 5:
            return None        
        else:
            return rows

    def printAPI(self):
        uris = self.db_query("SELECT request_uri, method, full_uri, id FROM uri")
        data = list()
        if not uris:
            return None, None, None, None
        else:
            for row in uris:
                querystrings = self.db_query("SELECT title FROM query_string where request = ?",(row[3],))
                headers = self.db_query("SELECT name FROM headers where request = ? AND response = 0", (row[3],))
                respheaders = self.db_query("SELECT name FROM headers where request = ? AND response = 1", (row[3],))
                uri = {"uri":row[0], "method":row[1], "querystrings":querystrings, "headers":headers, "respheaders": respheaders}
                data.append(uri)
            return data
'''        
            html = str()
            for row in uris:
            html += "||%s||%s||" % (row[1], row[0])
            querystrings = self.db_query("SELECT title FROM query_string where request = ?",(row[3],))
            if querystrings:
                html += "?"
                for qs in querystrings:
                    html += "%s=&lt;val&gt;&" % qs[0]
                html = html[:-1]
            html += "||"
            html +="<br>"
        return html

            html = html + "<h2>" + row[1] + " " + row[0] + "</h2>"
            querystrings = self.db_query("SELECT title FROM query_string where request = ?",(row[3],))
            if querystrings:
                html = html + "<h3>Query Strings:</h3><ul>"
                for qs in querystrings:
                    html += "<li>" + qs[0] + "</li>"
            
                html = html + "</ul>"
            headers = self.db_query("SELECT name FROM headers where request = ? AND response = 0", (row[3],))
            if headers:
                html = html + "<h3>Request headers:</h3><ul>"
                for header in headers:
                    html += "<li>" + header[0] + "</li>"
            
                html = html + "</ul>"
            headers = self.db_query("SELECT name FROM headers where request = ? AND response = 1", (row[3],))
            if headers:
                html = html + "<h3>Response headers:</h3><ul>"
                for header in headers:
                    html = html + "<li>" + header[0] + "</li>"
            
                html = html + "</ul>"
        return html
'''
