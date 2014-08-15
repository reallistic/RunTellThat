import requests
from xml.etree import ElementTree
from logger import logger
import platform, subprocess, os, shutil, time, urllib


class PMS:
    port = "32400"
    ip = "localhost"
    online = False
    hasStoredPrefs = False
    friendlyName = ""
    machineId = ""
    signInState = "unknown"
    myPlexUsername = ""
    mappedState = "unknown"
    authToken = ""
    pmsprocess = None

    def __init__(self, serverip = None):
        if serverip:
            self.ip = serverip.split(":")[0]
            if ":" in serverip:
                self.port = serverip.split(":")[1]
        self.checkPMSOnline()
        self.reloadPreferences()

    def checkPMSOnline(self):
        logger.debug("Checking if plex is online")
        try:
            r = requests.get("http://%s:%s/" % (self.ip, self.port), timeout=1)
            self.online = r.status_code == requests.codes.ok
            logger.debug("plex is online at http://%s:%s/" % (self.ip, self.port))
        except Exception, e:
            logger.info("Plex not online %s" % e)
            self.online = False

    def reloadPreferences(self, force = False):
        if self.online or force:
            try:
                r = requests.get("http://%s:%s/" % (self.ip, self.port))
                self.online = r.status_code == requests.codes.ok
                if self.online:
                    root = ElementTree.fromstring(r.content)
                    self.friendlyName = root.attrib("friendlyName")
                    self.machineId = root.attrib("machineIdentifier")
                    self.signInState = root.attrib("myPlexSigninState")
                    self.myPlexUsername = root.attrib("myPlexUsername")
                    self.mappedState = root.attrib("myPlexMappingState")
                    r = requests.get("http://%s:%s/myplex/account" % (self.ip, self.port))
                    root = ElementTree.fromstring(r.content)
                    self.authToken = root.attrib("authToken")
                    return self.getPreferences()
                else:
                    return False
            except Exception, e:
                logger.error("Error reloading preferences %s" % e)

        return False

    def getPreferences(self):
        return {"friendlyName":self.friendlyName,
                "machineIdentifier":self.machineId,
                "myPlexSigninState":self.signInState,
                "myPlexUsername":self.myPlexUsername,
                "myPlexMappingState":self.mappedState,
                "authToken":self.authToken
                }
    def startPMS(self, force = False):
        if not self.online or force:
            logger.debug("calling subprocess")
            if platform.system() == "Linux":
                self.pmsprocess = subprocess.Popen("/etc/init.d/plexmediaserver start", shell=True)
                #subprocess.call(["/etc/init.d/plexmediaserver", "start"])
            elif platform.system() == "Windows":
                self.pmsprocess = subprocess.Popen(r"C:\Program Files (x86)\Plex\Plex Media Server\Plex Media Server.exe")
                #subprocess.call([r"C:\Program Files (x86)\Plex\Plex Media Server\Plex Media Server.exe"])
            retries = 0
            while retries < 5 and not self.online:
                time.sleep(5)
                self.checkPMSOnline()
                retries+=1
        return self.online


    def stopPMS(self, force = False):
        if self.online or force:
            if self.pmsprocess:
                self.pmsprocess.kill()
                self.pmsprocess = None
            logger.debug("calling subprocess")
            if platform.system() == "Linux":
                #subprocess.call(["/etc/init.d/plexmediaserver", "stop"])
                self.pmsprocess = subprocess.Popen("/etc/init.d/plexmediaserver stop", shell=True)
            elif platform.system() == "Windows":
                self.pmsprocess = subprocess.Popen('taskkill /f /im "PlexScriptHost.exe"')
                self.pmsprocess = subprocess.Popen('taskkill /f /im "Plex Media Server.exe"')
                #os.system('taskkill /f /im "Plex Media Server.exe"')
        self.checkPMSOnline()
        return not self.online


    def restartPMS(self, force = False):
        if self.stopPMS(force):
            time.sleep(0.2)
            return self.startPMS(force)


    def restorePreferences(self, path):
        path = os.path.abspath(path)
        if self.pmsprocess:
            self.pmsprocess.kill()
            self.pmsprocess = None
        self.stopPMS(True)
        if os.path.isfile(path):
            if platform.system() == "Linux":
                    shutil.copy2(path, "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Preferences.xml")
            elif platform.system() == "Windows":
                try:
                    logger.debug("Importing key from %s" % path)
                    os.system(r'reg import %s' % path)
                except Exception, e:
                    logger.error("Couldn't import the PMS registry Preferences")
                    logger.error(e)
                    return False
        else:
            logger.error("Preferences backup file not found at %s" % path)
        return False

        return self.hasStoredPrefs
    def storePreferences(self, path):
        path = os.path.abspath(path)
        if platform.system() == "Linux":
            if os.path.isfile("/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Preferences.xml"):
                shutil.copy2("/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Preferences.xml", path)
                self.hasStoredPrefs = True
        elif platform.system() == "Windows":
            try:
                if os.path.isfile(path):
                    os.remove(path)
                logger.debug("Saving key to %s" % path)
                os.system(r'reg export "HKEY_CURRENT_USER\Software\Plex, Inc.\Plex Media Server" %s' % path)
                self.hasStoredPrefs = True
            except Exception, e:
                logger.error("Couldn't save the PMS registry Preferences")
                logger.error(e)
                self.hasStoredPrefs = False
        else:
            self.hasStoredPrefs = False

        return self.hasStoredPrefs

    def removePreferences(self):
        if platform.system() == "Linux":
            try:
                os.remove("/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Preferences.xml")
                return True
            except Exception, e:
                logger.error("Could not remove linux Preferences.xml")

        elif platform.system() == "Windows":
            try:
                os.system(r'reg delete "HKEY_CURRENT_USER\Software\Plex, Inc.\Plex Media Server" /f')
                return True
            except Exception, e:
                logger.error("Couldn't delete the PMS registry Preferences")
                logger.error(e)

        return False

    def setFriendlyName(self, name):
        if not self.online:
            return False
        else:
            try:
                r = requests.put("http://%s:%s/:/prefs?FriendlyName=%s" % (self.ip, self.port, name))
                return r.status_code == requests.codes.ok
            except Exception, e:
                logger.error("Error setting friendly name %s" % e)
        return False

    def setPreferences(self, prefs = {}):
        if not self.online:
            return False
        else:
            try:
                params = urllib.urlencode(prefs)
                r = requests.put("http://%s:%s/:/prefs?%s" % (self.ip, self.port, params))
                return r.status_code == requests.codes.ok
            except Exception, e:
                logger.error("Error setting Preferences %s" % prefs)
                logger.error(e)
        return False

    def mapTomyPlex(self, ipport = None):
        '''
        Map a PMS to myplex via the specified port

        Calls the api to map pms when online.
        ipport string optional: the port or ip:port to be mapped to.
        If the ip is included it is set for the current instance
        Return True on success or false on failure
        '''
        if not self.online:
            return False

        if ipport:
            if ":" in ipport:
                self.ip = ipport.split(":")[0]
                ipport = ipport.split(":")[1]
                logger.debug("Manual port %s" % ipport)
            if not self.setPreferences({"ManualPortMappingMode":"1","ManualPortMappingPort":ipport}):
                logger.debug("Failed ManualPortMappingMode")
                return False

        if not self.setPreferences({"PublishServerOnPlexOnlineKey":"true"}):
            logger.debug("failed publishing when online")
            return False
        mapped = "unknown"
        endmapping = ["mapped", "failed"]
        retries =0
        while mapped not in endmapping and retries <=5:
            time.sleep(0.5)
            prefs = self.reloadPreferences()
            if prefs:
                mapped = prefs["myPlexMappingState"]
            retries+=1

        return mapped == "mapped"

    def signIn(self, username, password):
        if not self.online:
            return False

        params = urllib.urlencode({"username":username, "password":password})
        logger.debug("logging in %s" % params)
        r = requests.put("http://%s:%s/myplex/account?%s" % (self.ip, self.port, params))
        if r.status_code == requests.codes.ok:
            root = ElementTree.fromstring(r.content)
            self.authToken = root.attrib["authToken"]
            logger.debug("Authtoken is %s" % self.authToken)
            return self.authToken
        else:
            return False