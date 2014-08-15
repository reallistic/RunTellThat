<?php
$token = ""; //MyPlex auth token of myplex user below
$username = ""; //username of the myplex user owning the PMS server that requests are proxied to
$lbip = ""; //IP or hostname (No port or protocol) of the PMS server having the same ip as the Load Balancer
$destserver = ""; //IP:port of the PMS server that requests are proxied to
$destserverre = $destserver; //REMOTE IP:port of the PMS server that requests are proxied to
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
$log = "/path/to/logs/changeup.log";
$loggingenabled = TRUE;
$loghistorylength = 5;
$maxlogsize = 1* 1024 * 1024; //1MB

$streamsize=10485760; //5MB. RTT Client streaming size. Not yet documented
$enablerttclientmode=FALSE;// RTT Client mode will stream media instead of redirecting.
//do not modify
$unm = "";
?>
