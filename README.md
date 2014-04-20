RunTellThat (for Plex)
============

Distributed computing implementation for plex

#What this is:
 - A MitM webserver to distribute or proxy access to arbitrary PMS nodes; A must-have for load-balancing shared access to a PMS cluster [which this hack facilitates]. 
 - A proxy to delegate channel access w/o permanently binding PMS to myPlex.
 - The foundation of a decent plex load balancer.
 - A new paradigm for plex sharing.
 - A special hack that indeed will probably never be "officially" supported.
 
#What this is **not**:
 - A hacking tool to steal someone's plex share or server.
 - A Plex Channel.
 
#Requirements
 - Apache 2.x
 - curl

#Installation
 Clone this repo into an apache webserver folder.
 ```
 $/var/www/plex/: clone https://github.com/rxsegrxup/RunTellThat.git
 ```
 Utilize the following VirtualHost
 ```
 <VirtualHost *:32400>
    ServerAdmin webmaster@localhost
    DocumentRoot /var/www/plex
    <Directory />
            Options FollowSymLinks
            AllowOverride All
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/halfhaxerror.log
    LogLevel warn
    CustomLog ${APACHE_LOG_DIR}/halfhaxaccess.log combined
</VirtualHost>
```
Be sure to enable Listening on port 32400
```
#apache2.conf OR ports.conf
NameVirtualHost *:32400
Listen 32400
```
Set the values in the config file. (More help below)
Start up apache and you're OFF!

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
 Ghost mode is a lot more complex as it requires a PMS server having the same IP as the RunTellThat (host) server.
 The idea, is that RunTellThat needs to have the same IP as PMS so that Plex.tv (MyPlex) knows to look at this IP for a PMS server.
 
