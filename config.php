<?php
$token = ""; //MyPlex auth token of myplex user below
$client = ""; //NOT USED -- client identifier of myplex user below
$username = ""; //username of the myplex user owning the PMS server that requests are proxied to
$lbip = ""; //IP or hostname (No port or protocol) of the PMS server having the same ip as the Load Balancer
$destserver = ""; //IP or hostname (No port or protocol) of the PMS server that requests are proxied to
$lbname = ""; //Friendly name of the PMS server having the same ip as the Load Balancer
$destname = ""; //Friendly name of the PMS server that requests are proxied to
//Get the values below from the /var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Preferences.xml
$lbuuidkvp = array(
    "PlexOnlineMail1" => "ProcessedMachineIdentifier1",
    "PlexOnlineMail2" => "ProcessedMachineIdentifier2",
    "PlexOnlineMail3" => "ProcessedMachineIdentifier3",);
//Get the values below from the /var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Preferences.xml
//Server requests are being proxied to
$destuuid = "ProcessedMachineIdentifier";
$unm = ""; //Place holder. Will be overwritten
$log = "/path/to/logs/changeup.log";
$loggingenabled = TRUE;
$loghistorylength = 5;