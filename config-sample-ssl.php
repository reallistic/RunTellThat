<?php
// Destination PMS Owner
$token = ""; //MyPlex auth token
//Can be found in /var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Preferences.xml
$username = ""; //username of the myplex user owning the PMS server that requests are proxied to
//Can be found in /var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Preferences.xml

// RTT/DummyPMS Server
$lbip = "<IP Address>:443"; //REMOTEIP:port of RTT
$lbname = ""; //Friendly name of the Dummy PMS server having the same ip as RTT

// Destination PMS
$destserver = ""; //IP:port of the PMS server that requests are proxied to
//$destserver = "localhost:32400" //If running RTT and PMS on the same server (use lan address if same lan)
$destserverre = $destserver; //REMOTE IP:port of the PMS server that requests are proxied to
//$destserverre = "REMOTEIP:REMOTEPORT" //Only use this if using lan ip for $destserver
//Get the values below from the /var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Preferences.xml
$destname = ""; //Friendly name of the PMS server that requests are proxied to
$destuuid = "ProcessedMachineIdentifier";

// Proxied Users
$lbuuidkvp = array(
    "PlexOnlineMail1" => "ProcessedMachineIdentifier1",
    "PlexOnlineMail2" => "ProcessedMachineIdentifier2",
    "PlexOnlineMail3" => "ProcessedMachineIdentifier3",
    $username => $destuuid);
//Get the values below from the /var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Preferences.xml
//Server requests are being proxied to

// Config
$log = "/path/to/logs/changeup.log";
$loggingenabled = TRUE;
$loghistorylength = 5;
$maxlogsize = 1* 1024 * 1024; //1MB

// RTT Client Mode
// RTT Client mode will allow proxied media playback
$swapidentity = FALSE; //Should the identity of the user be swapped with ther owner. Disable for general proxy
$namedusersonly = FALSE; //Only allow users within the $lbuuidkvp array through.
//When swapidentity is FALSE, disable to let PMS manage permissions.
//When $enableanonymousaccess is TRUE, enable to limit user access.
$blocksections = FALSE; //DO NOT allow access to sections. (TRUE to disable client mode || FALSE to enable client mode)
$streamsize=10485760; //5MB. RTT Client streaming size. Not yet documented
$clientstreaming=TRUE; //Used with Client mode. Will stream media instead of redirecting.
// DANGER: redirecting is dangerous when used with swapidentity. This WILL 100% expose the super user account

// DANGER ZONE
$enableanonymousaccess=FALSE; //DANGER! DANGER! this will essentially open up the proxied server to ANY and EVERY myPlex user that knows the ip.
//Enable only if you know what you are doing.
?>