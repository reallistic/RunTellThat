RunTellThat (for Plex)
============

Distributed computing implementation for plex. Documentation/Explanation is [here] (https://docs.google.com/drawings/d/1gv_1zGANUaoiXvKYSVKILGWWNoUYZ9ajWIo3Z76XEps/edit?usp=sharing)

#Current support:
Currently RTT only supports proxy of requests to a designated PMS. This is best suited for sharing channels or providing an super user experience for a shared user. This is helpful for an application like [Serenity] (https://forums.plex.tv/index.php/forum/135-serenity-for-android/) which does not support myPlex shares.<br>
[Here are instructions] (https://github.com/rxsegrxup/RunTellThat/wiki/Setup-Guide-to-Share-Channels)

#What this is:
 - A MitM webserver to distribute or proxy access to arbitrary PMS slaves; A must-have for load-balancing shared access to a PMS cluster [which this hack facilitates]. 
 - A proxy to delegate channel access w/o permanently binding PMS to myPlex.
 - The foundation of a decent plex load balancer.
 - A new paradigm for plex sharing.
 - A special hack that indeed will probably never be "officially" supported.
 
#What this is **not**:
 - A hacking tool to steal someone's plex share or server.
 - A Plex Channel.
 - Chuck Norris's PMS farm
 
##Please see the [FAQ] (https://github.com/rxsegrxup/RunTellThat/wiki/FAQ)

#Requirements
 - Apache 2.x
 - curl
 - ifstat (load balancing)
 - python 2.7 (load balancing/PMS)
 
#Pre-Istallation
A few things are assumed about your setup & usage of Plex prior to utilizing RTT:
 - You ideally have 3 or more separate servers, with/without identical instances of PMS (in terms of library sections & channels installed) that you would like to incorporate in a distributed computing model where: 'server1' (let's call this the Master), recieves and funnels requests to 'server2' OR 'server3', depending on the current CPU/Network load of these machines (known as 'Slaves').
 - You have # or more Plex.tv accounts ____
 
#Installation
 Clone this repo into an apache webserver folder on your Master/proxy server.
 ```
 webuser@master:/var/www/plex# git clone https://github.com/rxsegrxup/RunTellThat.git
 webuser@master:/var/www/plex# mv RunTellThat/* ./
 ```
 Utilize the following VirtualHost
 ```
 <VirtualHost *:32401>
    ServerAdmin webmaster@localhost
    DocumentRoot /var/www/plex
    <Directory />
            Options FollowSymLinks
            AllowOverride All
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/rtterror.log
    LogLevel warn
    CustomLog ${APACHE_LOG_DIR}/rttaccess.log combined
</VirtualHost>
```
Be sure to enable Listening on port 32401 (or whatever port you like)
```
#apache2.conf OR ports.conf
NameVirtualHost *:32401
Listen 32401
```
Set the values in the config file. (More help below)
Enable mod_rewrite
```
a2enmod rewrite
```
Start up apache and you're OFF!
When installation is finished, verify that apache is running and actively listening on incoming port 32401.

#How to use 
 There are two modes that this is accessible in. Lets call them IP mode, and Ghost mode.<br>
 <br>
 **IP Mode**:
 <br>
 IP mode is the simplest way to utilize this.
 This is done by manually configuring a plex server and for the hostname/ip use that of the RunTellThat server.
 Or, simply navigate to RunTellThat's server and log in as if you would normally access a plex web server.
 <br>
 **Ghost Mode**
 <br>
 Ghost mode is a lot more complex as it requires a PMS server having the same IP as the RunTellThat (host) server to be owned by all end-users. The idea, is that by RunTellThat having the same IP as PMS Plex clients will know to look for a PMS server at this IP and when it finds RTT, RTT will forwards it to the destination. To do this, you must install PMS on the master/proxy server and map it to every user that will be accessing your content via RTT.
 
#Ghost mapping 
**DummyPMS mapping on windows**
<br>
* Quit PMS
* start -> regedit.exe (search or use cmd)
* navigate to and delete HKEY_CURRENT_USER\Software\Plex, Inc.\Plex Media Server
* (leave regedit open)
* start pms
* Accept EULA
* set friendlyName to DummyPMS
* map pms server to a user at manual port 32401
* retrive and store username=>machineid combo by accessing http://localhost:32400/ or use the registry key ProcessedMachineIdentifier
* export (save) HKEY_CURRENT_USER\Software\Plex, Inc.\Plex Media Server as usernamePrefs.reg
* repeat

**DummyPMS mapping on linux**
<br>
* stop plexmediaserver
* delete /var/lib/plexmediaserver/Library/Application Support/Preferences.xml
* start pms
* Accept EULA
* set friendlyName to DummyPMS
* map pms server to a user at manual port 32401
* retrive and store username=>machineid combo by accessing http://localhost:32400/ or use the new Preferences.xml
* backup the Preferences.xml as username.Preferences.xml
* repeat

#Using the config file
```
//config.php


//user name of the destination server's myPlex owner
//Can be found in Preferences.xml
$username = "";

//authToken of the destination server's myPlex owner
//Can be found in Preferences.xml
$token = "";

//global ip address:port of the current RTT server
$lbip = "123.123.123.123:32401";

//ipaddress:port of the destination server
$destserver = "123.123.123.321:32400";

//ipaddress:port of the destination server for RTT client streaming redirect
//not used/documented
$destserverre = "123.123.123.321:32400";

//friendlyName of dummyPMS server
$lbname = "DummyPMS";

//friendlyName of destination PMS server
$destname = "PMSSlave";
$lbuuidkvp = array(
       "username"=>"uuid",
       "username2"=>"uuid2"
    );
//machineIdentifier of the destination pms slave server
//FUTURE: array of "friendlyName"=>"uuid" pairs
$destuuid = "";

//initialize var
$unm = "";

//configure logging
$log = "/var/log/rtt/rtt.log";
$loggingenabled = TRUE;
$loghistorylength = 5;
$maxlogsize = 1* 1024 * 1024; //1MB

//RTT Client streaming. not used/documented
$streamsize=10485760; //5MB
```
