import ConfigParser, os, socket, requests
from xml.etree import ElementTree

CONFIGFILE = "rttserver.ini"
config = None
def getInfoFromPMS():
    r = requests.get("http://localhost:32400/")
    data = {
        "friendlyName":socket.gethostname(),
        "machineIdentifier":"",
        "myPlexUsername":"",
        "authToken":"",
        "publicPort":"32400",
        "ip": "localhost"
    }
    if r.status_code == 200:
        root = ElementTree.fromstring(r.text)
        data = {
            "friendlyName":root.attrib["friendlyName"],
            "machineIdentifier":root.attrib["machineIdentifier"],
            "myPlexUsername":root.attrib["myPlexUsername"],
            "authToken":"",
            "publicPort":"32400"
        }
        r = requests.get("http://localhost:32400/myplex/account")
        if r.status_code == 200:
            root = ElementTree.fromstring(r.text)
            try:
                data["authToken"] = root.attrib["authToken"]
                data["publicPort"] = root.attrib["publicPort"]
            except Exception, e:
                pass

    r = requests.get("https://plex.tv/pms/:/ip")
    if r.status_code == 200:
        data["ip"] = r.text.rstrip()
    return data

def readConfig():
    global config
    data = dict()
    Config = ConfigParser.ConfigParser()
    Config.optionxform = str
    Config.read("rttserver.ini")
    try:
        for section in Config.sections():
            data[section] = dict()
            for key, item in Config.items(section):
                data[section][key] = item
    except Exception, e:
        print "Error reading config. Recreating"
        return createConfig()

    return data

def setConfig(data):
    global config
    print "Saving config file"
    Config = ConfigParser.ConfigParser()
    Config.optionxform = str
    cf = open(CONFIGFILE, 'w')
    for section in data.keys():
        Config.add_section(section)
        for key, item in data[section].items():
            Config.set(section, key, item)

    if "Debug" not in data["Logging"]:
        Config.set("Logging", "Debug", False)
    if "Enabled" not in data["Logging"]:
        Config.set("Logging", "Enabled", False)
    Config = createTypes(Config)
    Config.write(cf)
    cf.close()
    config = readConfig()
    return config

def createTypes(Config):
    Config.set("RestrictedUris", 'Type', "list")
    Config.set("RedirectedUris", "Type", "list")
    Config.set("FilterHeaders", "Type", "list")
    Config.set("Logging", "Type", "")
    Config.set("UserMachineIdentifiers", "Type", "dict")
    Config.set("RTTServer", 'Type', "")
    Config.set("RTTClient", "Type", "")
    Config.set("SuperUser", 'Type', "")
    return Config

def createConfig():
    print "Creating config"
    Config = ConfigParser.ConfigParser()
    Config.optionxform = str
    cf = open(CONFIGFILE, 'w')

    #Sensitive sections that shouldn't be accesible
    Config.add_section("RestrictedUris")
    Config.set("RestrictedUris", 'RestrictedUris1', "/status/sessions")
    Config.set("RestrictedUris", 'RestrictedUris2', "/prefs")
    Config.set("RestrictedUris", 'RestrictedUris3', "/system/appstore")
    Config.set("RestrictedUris", 'RestrictedUris4', "/:/websockets/")

    #Urls causing a lot of network IO that should be redirected
    Config.add_section("RedirectedUris")
    Config.set("RedirectedUris", "RedirectedUris1", "/library/parts/")
    Config.set("RedirectedUris", "RedirectedUris2", "/video/:/transcode/")

    #Headers that cause ther hop by hop exception must be filtered out
    Config.add_section("FilterHeaders")
    Config.set("FilterHeaders", "FilterHeaders1", "connection")
    Config.set("FilterHeaders", "FilterHeaders2", "keep-alive")
    Config.set("FilterHeaders", "FilterHeaders3", "proxy-authenticate")
    Config.set("FilterHeaders", "FilterHeaders4", "proxy-authorization")
    Config.set("FilterHeaders", "FilterHeaders5", "te")
    Config.set("FilterHeaders", "FilterHeaders6", "transfer-encodinga")
    Config.set("FilterHeaders", "FilterHeaders7", "upgrade")
    Config.set("FilterHeaders", "FilterHeaders8", "content-length")
    Config.set("FilterHeaders", "FilterHeaders9", "content-encoding")

    #Logging
    Config.add_section("Logging")
    Config.set("Logging", "Enabled", True)
    Config.set("Logging", "FilePath", "rttserver.log")
    Config.set("Logging", "Debug", False)
    Config.set("Logging", "MaxSize", 1*1024*1024) #1MB
    Config.set("Logging", "MaxFiles", 5)

    #user machine identifer pairs
    Config.add_section("UserMachineIdentifiers")


    data = getInfoFromPMS()
    if data["myPlexUsername"] and data["machineIdentifier"]:
        Config.set("UserMachineIdentifiers", data["myPlexUsername"], data["machineIdentifier"])
    #General server settings
    Config.add_section("RTTServer")
    Config.set("RTTServer", 'ServerIP', "localhost:32401")
    Config.set("RTTServer", 'FriendlyName', "RTTServer")
    Config.set("RTTServer", 'Host', "0.0.0.0")
    Config.set("RTTServer", 'Port', "32401")
    Config.set("RTTServer", "PrefBackupLocation", "prefs/")

    #User that owns the destination server
    Config.add_section("SuperUser")
    Config.set("SuperUser", 'Username', data["myPlexUsername"])
    Config.set("SuperUser", 'AuthToken', data["authToken"])

    #DestinationServer
    Config.add_section("RTTClient")
    Config.set("RTTClient", "ServerIP", "localhost:32400")
    Config.set("RTTClient", "PublicServerIP", "%s:%s" % (data["ip"], data["publicPort"]))
    Config.set("RTTClient", 'FriendlyName', data["friendlyName"])
    Config.set("RTTClient", 'MachineIdentifier', data["machineIdentifier"])
    Config = createTypes(Config)
    Config.write(cf)
    cf.close()
    return readConfig()

if os.path.isfile(CONFIGFILE):
    config = readConfig()
else:
    config = createConfig()

descriptions = dict()
descriptions["FilterHeaders"] = "Headers that need to be filtered to prevent hop by hop error"
descriptions["RestrictedUris"] = "Uri parts that should not be accessible by end-users"
descriptions["RedirectedUris"] = "Uri parts that should not be proxied but redirected instead"
descriptions["Logging"] = dict()
descriptions["Logging"]["FilePath"] = "Path to the log file"
descriptions["Logging"]["Debug"] = "Enable debug log mode and BottlePy debug mode"
descriptions["Logging"]["MaxSize"] = "Log max size in bytes"
descriptions["Logging"]["MaxFiles"] = "Number of history files to keep"
descriptions["UserMachineIdentifiers"] = "Pairs of plex usernames and their ghosted server MachineIdentifier"
descriptions["RTTServer"] = dict()
descriptions["RTTServer"]["ServerIP"] = "Public IP:port of the RTTServer. (can be localhost:32401 if in dev or a localhost env)"
descriptions["RTTServer"]["FriendlyName"] = "The friendlyname of the Ghosted PMS servers pointing to RTTServer"
descriptions["RTTServer"]["Host"] = "The host address for RTTServer to listen on"
descriptions["RTTServer"]["Port"] = "The port for RTTServer to listen on"
descriptions["SuperUser"] = dict()
descriptions["SuperUser"]["Username"] = "Username of the user owning the destination RTTClient PMS server"
descriptions["SuperUser"]["AuthToken"] = "The myPlex AuthToken of the user owning the destination RTTClient PMS server"
descriptions["RTTClient"] = dict()
descriptions["RTTClient"]["ServerIP"] = "IP:port of the RTTClient. (localhost:32400 for single server environment)"
descriptions["RTTClient"]["PublicServerIP"] = "Public IP:port of the RTTClient.  (can be localhost:32400 if in dev or a localhost env)"
descriptions["RTTClient"]["FriendlyName"] = "The friendlyname of the destination RTTClient PMS server"
descriptions["RTTClient"]["MachineIdentifier"] = "The MachineIdentifier of the destination RTTClient PMS server"

print "Config loaded"

'''
username = "reallistic"
token = "wB27RCZKMDvaqk5qriau"
#lbip = "192.187.100.203:32401"
lbip = "50.190.145.172:32401"
#// n2 $destserver = "localhost:32400"
#// n2 $destserverre = "192.187.100.203:32400"
#destserver = "slave1.plexcloud.tv:32400"
#destserverre = "slave1.plexcloud.tv:32400"
destserver = "localhost:32400"
destserverre = "50.190.145.172:32400"
lbname = "PE"
lbname = "reallistic-pc"
#//$destname = "n2"
destname = "slave1"
destname = lbname
useruuidpairs = {
    "admin@plexcloud.tv" : "e06ff391180801738ff4a5cfb2b1efb823d37782",
    "jercon@plexcloud.tv" : "556bf8f0216e66edb68ca99666b74e01868aa7f4", #//****dup****//
    "rogerhobbs1@plexcloud.tv" : "82be4e1da4e44b3e881a0f5e8cbeb8560e3d7222", #//****dp****//
    "tai4lf08@plexcloud.tv" : "e54c116d90a4a294493c01df3aa5abe2de41c618",# //****dup****//
    "aun001@plexcloud.tv" : "96eac6e77bb6b707592b52241d1cfd05b696690f", #//****dup****//
    "roo001@plexcloud.tv" : "7a20921607d32776f74f203d67b399b003264b30", #//****dup****//
    "allmcc@plexcloud.tv" : "89daed5813d50621821acd0ff68c62c955a58250", #//****dup****//
    "plexcloud.tv" : "251eb913a5b6e8b27a45d792852f999865ba7181",
    "robnsn@plexcloud.tv":"ca2692503ef5db1e768ed06b7fadc5799ce75948",
    "wordlife62392@plexcloud.tv":"428dcf8a87a2796647e8c6b41498cba50c9e6b80",
    "roger@plexcloud.tv":"b4f6252cdbee51fa19bc66e7bf66e0ae17e00dce",
    "regularchef@plexcloud.tv":"868f468bfd5b162fee5f818b692c959a76ad456f",
    "marcul@plexcloud.tv":"f4e0574cca0901ecd2472276d3fc9ebacf0fbd34",
    "marbro0@plexcloud.tv":"7d2c0d8b86924b0f37056f1275829e31f75f281a",
    "kamgeo@plexcloud.tv":"03477bf89d661b3261ee7d407800a27a67e01f24",
    "justin@plexcloud.tv":"b492cd5dca65b4d24de7e949144c15df69d71103",
    "josfor2@plexcloud.tv":"3bf839fa81083bc082851f0881a94116a56bdcf1",
    "josfor1@plexcloud.tv":"54d9068707e9247516cd7bda96e54f80b3007b92",
    "jaylin@plexcloud.tv":"da752a475817cae3f4148f9b03cdd86016154697",
    "brandon@plexcloud.tv":"57078712d1f127987d5431a3c9a9e3583e78fa20",
    "antoinette@plexcloud.tv":"3834106293ae2b5179c525da867845bcef4aed47",
    "reallistic" : "8f452b27df92b2c41a49cb80c1995f502f27a644"}
#// n2 $destuuid = "999ab75ea940faefc0d5afc9b247a2e90b07bbf8"
destuuid = "251eb913a5b6e8b27a45d792852f999865ba7181"
destuuid = "e2f6841f31e221f85cb6ffef24ec3076269651ff"
destuuid = "2bd4c5a823b8ba5b88973ad88a6bf8624b08e6e4"
log = "changeup.log"
loggingenabled = True
loghistorylength = 5
maxlogsize = 1* 1024 * 1024 #//1MB
streamsize=10485760 #//5MB

restricteduris = ["/:/prefs","/status/sessions", "/prefs", "/system/appstore", "/:/websockets/"]
redirecturis = ["/library/parts/", "/video/:/transcode/"]
FILTER_HEADERS = [
    'connection',
    'keep-alive',
    'proxy-authenticate',
    'proxy-authorization',
    'te',
    'trailers',
    'transfer-encoding',
    'upgrade',
    'content-length',
    'content-encoding'
    ]
'''