from bottle import route, run, request, get, post, template, response, view, static_file
import bottle, requests
from config import config, descriptions as configd, setConfig
from xml.etree import ElementTree
import zlib, urllib, traceback
from logger import logger
from apilogger import ApiLogger
from PMS import PMS
import sys, os, platform

@route('/static/<filepath:path>')
def static(filepath):
    return static_file(filepath, root='static')

@route('/apilog')
@route('/apilog/')
def apilog():
    try:
        apilogger = ApiLogger()
        data = apilogger.printAPI()
        return template("apilogger", data=data)
    except:
        tb = traceback.format_exc()
        logger.error("Error printing from ApiLogger")
        logger.error(tb)
    return "An error occured"

@route('/config', method='POST')
@route('/config/', method='POST')
def configpost():
    global config
    newconfig = dict()
    for key in request.forms.keys():
        if not "[]" in key:
            tkey = key.split("_")
            section = tkey[0]
            skey = tkey[1]
            if section not in newconfig:
                newconfig[section] = dict()
            val = request.forms.get(key)
            newconfig[section][skey] = val
            logger.info("%s %s %s" % (section, skey, val))
        elif "_key[]" in key:
            tkey = key[:-6]
            if tkey not in newconfig:
                newconfig[tkey] = dict()
            vkey = "%s%s" % (tkey, "_value[]")
            for val in request.forms.getall(vkey):
                skey = request.forms.getall(key)[len(newconfig[tkey])]
                newconfig[tkey][skey] = val
                logger.info("%s %s %s" % (tkey, skey, val))
        elif "_value[]" not in key:
            tkey = key[:-2]
            if tkey not in newconfig:
                newconfig[tkey] = dict()            
            for val in request.forms.getall(key):
                skey = "%s%s" % (tkey, len(newconfig[tkey]))
                newconfig[tkey][skey] = val
                logger.info("%s %s %s" % (tkey, skey, val))
    config = setConfig(newconfig)
    return template("settings", config=config, desc=configd)

@route('/ghost/', method='POST')
def ghostpost():
    step = 1
    uname=request.forms.username
    pw=request.forms.password
    data = None
    retdata = None
    path = os.path.join(config["RTTServer"]["PrefBackupLocation"], "baseprefs.reg")
    helper = PMS()
    logger.debug("backing up and removing preferences %s" % path)
    try:
        if helper.storePreferences(path) and helper.removePreferences():
            step+=1 #2
            logger.debug("force Restart pms")
            if helper.restartPMS(True):
                step+=1 #3
                logger.debug("Setting eula accept and collect data")
                if helper.setPreferences({"AcceptedEULA":"true", "collectUsageData":"0"}):
                    step+=1 #4
                    logger.debug("signing in with %s xxxx" % uname)
                    if helper.signIn(uname, pw):
                        step+=1 #5
                        logger.debug("Setting friendly name")
                        helper.setFriendlyName(config["RTTServer"]["FriendlyName"])
                        logger.debug("Mapping to myplex using %s" % config["RTTClient"]["PublicServerIP"])
                        if helper.mapTomyPlex(config["RTTClient"]["PublicServerIP"]):
                            step+=1 #6
                            logger.debug("map successful")
                            if helper.reloadPreferences():
                                step+=1 #7
                                logger.debug("Reloading preferences")
                                data = helper.getPreferences()

        if data:
            logger.debug("Got id and username data %s:%s" % (data["myPlexUsername"], data["machineIdentifier"]))
            config["UserMachineIdentifiers"][data["myPlexUsername"]] = data["machineIdentifier"]
            userpath = os.path.join(config["RTTServer"]["PrefBackupLocation"], "%sprefs.reg" % data["myPlexUsername"] )
            if helper.storePreferences(path) and helper.removePreferences():
                data["error"]=""
                retdata = data
    except Exception, e:
        logger.error(e)
        pass
    logger.debug("restoring original preferences")
    helper.stopPMS(True)
    helper.restorePreferences(path)
    
    if not retdata:
        retdata = {"error":"Error mapping to myPlex at step " + str(step)}
    return retdata

@route('/config')
@route('/config/')
def configpage():
    return template("settings", config=config, desc=configd)

@route('/', method='ANY')
@route('/<uri:path>', method='ANY')
def proxy(uri=""):
    uri = "/%s" % uri
    logger.debug("%s %s" % (request.method, request.url))
    rtt = RTTServer(uri)
    resp = rtt.proxy()
    for param,val in resp.headers.items():
        if param.lower() not in config["FilterHeaders"].values():
            logger.debug("adding header %s: %s" % (param,val))
            response.set_header(param,val)
        else:
            logger.debug("Prevent hop by hop for header: %s" % param)
    response.status = resp.status
    try:
        apilogger = ApiLogger()
        apilogger.LOG(request, response)
    except:
        tb = traceback.format_exc()
        logger.error("Error in ApiLogger")
        logger.error(tb)
    return resp.body
    
class RTTServer:
    username = ""
    usertoken = ""
    acceptr = False
    accepteh = False

    def __init__(self, request_uri):
        self.request_uri = request_uri
        self.request_method = request.method
        self.query_string = request.query
        self.headers = request.headers

    def getUsername(self):
        headers = {"X-Plex-Token":self.usertoken}
        r = requests.get("https://plex.tv/users/account", headers=headers)
        root = ElementTree.fromstring(r.content)
        for username in root.findall('username'):
            self.username = username.text

    def fixQuery(self):
        query_string=dict()
        for param,val in self.query_string.items():
            if param == "X-Plex-Token":
                logger.info("Found user token %s" % val)
                self.usertoken = val
                logger.info("Fixing url part %s = %s" % (param,val))
                val = config["SuperUser"]["AuthToken"]
            elif param == "X-Plex-Username":
                logger.info("Found username %s" % val)
                self.username = val
                val = config["SuperUser"]["Username"]
                logger.info("Fixing url part %s = %s" % (param,val))
            elif param == "Referer" or param == "Host" or param == "Origin":
                val = val.replace(config["RTTServer"]["ServerIP"], config["RTTClient"]["ServerIP"])
                logger.info("Fixing url part %s = %s" % (param,val))

            query_string[param]=val

        self.query_string = query_string

    def isRestricted(self):
        if any( sub in self.request_uri for sub in config["RestrictedUris"].values()):
            logger.info("Blocking %s" % self.request_uri)
            return True
        else:
            return False

    def fixHeaders(self):
        headers = dict()
        for param,val in self.headers.items():
            if param == "X-Plex-Token":
                logger.info("Found user token %s" % val)
                self.usertoken = val
                logger.info("Fixing header %s: %s" % (param,val))
                val = config["SuperUser"]["AuthToken"]
            elif param == "X-Plex-Username":
                logger.info("Found username %s" % val)
                self.username = val
                val = config["SuperUser"]["Username"]
                logger.info("Fixing header %s: %s" % (param,val))
            elif param == "Referer" or param == "Host" or param == "Origin":
                val = val.replace(config["RTTServer"]["ServerIP"], config["RTTClient"]["ServerIP"])
                logger.info("Fixing header %s: %s" % (param,val))
            if "Accept" in param and "gzip" in val:
                self.acceptr = True

            headers[param]=val
        self.headers=headers

    def isStream(self):
        if any( sub in self.request_uri for sub in config["RedirectedUris"].values()):
            logger.info("Switching to direct stream")
            return True
        else:
            return False

    def parseResponse(self, r):
        status = r.status_code
        logger.debug("status is %s" % status)
        headers = dict()
        for param, val in r.headers.items():
            if "Content" in param and "gzip" in val:
                self.accepteh = True
            elif config["RTTClient"]["ServerIP"] in val:
                logger.info("Fixing response header %s" % param)
                val = val.replace(config["RTTClient"]["ServerIP"], config["RTTServer"]["ServerIP"])
            logger.debug("found header %s: %s" % (param,val))
            headers[param]=val

        content = r.content

        if ('friendlyName="%s"' % config["RTTClient"]["FriendlyName"]) in content:
            logger.info("Swapping back friendlyName")
            content.replace(('friendlyName="%s"' % config["RTTClient"]["FriendlyName"]), ('friendlyName="%s"' % config["RTTServer"]["FriendlyName"]))

        elif ('machineIdentifier="%s"' % config["RTTClient"]["MachineIdentifier"]) in content:
            logger.info("Swapping back machineIdentifier")
            try:
                content.replace(('machineIdentifier="%s"' % config["RTTClient"]["MachineIdentifier"]),
                    ('machineIdentifier="%s"' % config["UserMachineIdentifiers"][self.username]))
            except KeyError, e:
                logger.warn("Key error while looking for machineIdentifier for user %s" % self.username)

        elif ('myPlexUsername="%s"' % config["SuperUser"]["Username"]) in content:
            logger.info("Swapping back myPlexUsername")
            content.replace(('myPlexUsername="%s"' % config["SuperUser"]["Username"]), ('myPlexUsername="%s"' % self.username))

        elif ('username="%s"' % config["SuperUser"]["Username"]) in content:
            logger.info("Swapping back username")
            content.replace(('username="%s"' % config["SuperUser"]["Username"]), ('username="%s"' % self.username))

        elif ('authToken="%s"' % config["SuperUser"]["AuthToken"]) in content:
            logger.info("Swapping back authToken")
            content.replace(('authToken="%s"' % config["SuperUser"]["AuthToken"]), ('authToken="%s"' % self.usertoken))

        if self.accepteh:# and self.acceptr:
            logger.info("Detected gzip encoding")
            content = zlib.compress(content)
        return bottle.Response(body=content, status=status, headers=headers)


    def proxy(self):
        if self.isRestricted():
            return bottle.Response(body="", status=401)
        elif self.isStream():
            location = "http://%s%s?%s" % (config["RTTClient"]["PublicServerIP"], self.request_uri,urllib.urlencode(self.query_string))
            logger.info("Redirect %s %s" % (self.request_method,location))
            headers = dict()
            for param, val in self.headers.items():
                headers[param]=val
            headers["Location"] = location
            return bottle.Response(body="", status=303, headers=headers)
        else:
            self.fixQuery()
            self.fixHeaders()
            if not self.username and self.usertoken:
                self.getUsername()
            if len(self.query_string) > 0:
                finalurl = "http://%s%s?%s" % (config["RTTClient"]["ServerIP"], self.request_uri,urllib.urlencode(self.query_string))
            else:
                finalurl = "http://%s%s" % (config["RTTClient"]["ServerIP"], self.request_uri)
            logger.info("Proxy %s %s" % (self.request_method,finalurl))
            try:
                r = getattr(requests,self.request_method.lower())(finalurl, data=self.query_string, headers=self.headers)
                return self.parseResponse(r)
            except Exception, e:
                logger.error("Error with request: %s" % e)
                return bottle.Response(body="", status=404)

run(host=config["RTTServer"]["Host"], port=config["RTTServer"]["Port"], debug=config["Logging"]["Debug"])
