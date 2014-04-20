<?php
//v1.0
try{
    require 'config.php';
}
catch (Exception $e){
    error_log ( "Error with PMS Load Balancer in ".__FILE__." at line 3. Unable to get config");
    exit;
}
$unm = "";
if($loggingenabled && !touch($log)){
    $loggingenabled = FALSE;
}
elseif($loggingenabled){
    $logdir = dirname($log);
    $logfilename = basename($log);
    if(!is_int($loghistorylength)){
        $tmp = $loghistorylength;
        $loghistorylength = 5;
        //resulting to default max length
        logger("got incorrect log max lenth $tmp using default 5");
        unset($tmp);
    }
}

function logger($data){
    global $log,$loggingenabled;
    if(!$loggingenabled){
        return;
    }
    $today = date("Y-m-d H:i:s");
    file_put_contents($log,"[$today]: $data\r\n",FILE_APPEND);
    if(filesize($log) > 1* 1024 * 1024){ //1 MB
        logrotate();
    }
}

function logrotate(){
    global $logdir,$logfilename,$log,$loghistorylength;
    $logfiles = scandir($logdir);
    $numlogs=1;
    foreach ($logfiles as $file) {
        if(stripos($file, $logfilename) !== FALSE){
            $numlogs++;
            if($numlogs > $loghistorylength){
                unlink("$logdir/$file");
            }
            else{
                rename("$logdir/$file", "$log.$numlogs");
            }
        }
    }
    rename($log, "$log.1");
    touch($log);
}

function replaceCookie($value, $repl){
    $cookies = explode(";",$value);
    $toreplace = "";
    foreach ($cookies as $cookie) {
        $kvp = explode("=", trim($cookie));
        if($kvp[0] == "SESSION-GUID"){
            $toreplace = $kvp[1];
            break;
        }
    }
    if($toreplace != ""){
        return str_replace($toreplace, $repl, $value);
    }
    else{
        return $value;
    }
}

function fixRequestUri($uri){
    global $token, $username, $lbip, $destserver, $unm;//, $client
    $uriparts = explode("?", $uri);
    if(count($uriparts)>1){
        $newuri = $uriparts[0]."?";
        $uriq = $uriparts[1];
    }
    else{
        return $uri;
    }

    $queryparts = explode("&", $uriq);
    $firstrun = TRUE;
    foreach ($queryparts as $query) {
        $kvp = explode("=", trim($query));
        switch ($kvp[0]) {
            case 'X-Plex-Token':
                $kvp[1] = $token;
                logger("fixing url part ".$kvp[0]."=".$kvp[1]);
            break;
            case 'X-Plex-Username':
                $unm = $kvp[1];
                $kvp[1] = $username;
                logger("fixing url part ".$kvp[0]."=".$kvp[1]);
            break;
            case 'Referer':
            case 'Host':
            case 'Origin':
                $kvp[1] = str_replace($lbip,$destserver, $kvp[1]);
                logger("fixing url part ".$kvp[0]."=".$kvp[1]);
            break;
            /*
              //In my tests I found that the client identifier doesnt much matter.
              //Only the username and token needs to be changed
            case 'Cookie':
                $value = replaceCookie($value, $client);
            break;
            case 'X-Plex-Client-Identifier':
                $value = $client;
            break;*/
        }
        if($firstrun === TRUE){
            $firstrun = FALSE;
            $newuri .= $kvp[0]."=".$kvp[1];
        }
        else{
            $newuri .= "&".$kvp[0]."=".$kvp[1];
        }
    }
    return $newuri;
}

$headers = array();
$accepteh=FALSE;
$acceptr=FALSE;

logger($_SERVER['REQUEST_METHOD']);
logger($_SERVER['REQUEST_URI']);
$ruri = fixRequestUri($_SERVER['REQUEST_URI']);
logger("http://$destserver:32400$ruri");
foreach (getallheaders() as $name => $value) {
    switch ($name) {
        case 'X-Plex-Token':
            logger("fixing $name");
            $value = $token;
        break;        
        case 'X-Plex-Username':
            logger("fixing $name");
            $unm = $value;
            $value = $username;
        break;
        case 'Referer':
        case 'Host':
        case 'Origin':
            logger("fixing $name");
            $value = str_replace($lbip,$destserver, $value);
        break;
        /*
          //In my tests I found that the client identifier doesnt much matter.
          //Only the username and token needs to be changed
        case 'Cookie':
            $value = replaceCookie($value, $client);
        break;
        case 'X-Plex-Client-Identifier':
            $value = $client;
        break;*/
    }
    if(stripos($name,"Accept") !== FALSE && stripos($value,"gzip") !== FALSE){
        //Detect gzip encoding
        $acceptr=TRUE;
    }
    logger("adding $name $value");
    $headers[] = "$name: $value";
}
logger("");


$ch = curl_init("http://$destserver:32400$ruri");
curl_setopt($ch,CURLOPT_ENCODING, '');
curl_setopt($ch,CURLOPT_RETURNTRANSFER,true);
curl_setopt($ch,CURLOPT_VERBOSE,1);
curl_setopt($ch, CURLOPT_HEADER, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $_SERVER['REQUEST_METHOD']);
$output = curl_exec($ch);

//Get the response code before closing curl
$httpCode = curl_getinfo ( $ch, CURLINFO_HTTP_CODE );
curl_close($ch);

//Split the response to retreive headers
list($header, $body) = explode("\r\n\r\n", $output, 2);
$header = explode("\r\n",$header);

//Send response code
http_response_code(intval($httpCode));
$firstrun = TRUE;



logger($httpCode);
logger($_SERVER['REQUEST_URI']);
logger("http://$destserver:32400$ruri");
foreach($header as $value){
    if($firstrun === TRUE){
        //The first header is always HTTP 1/1 CODE
        //Sending this this messes things up
        $firstrun = FALSE;
        continue;
    }
    if(stripos($value,"Content") !== FALSE && stripos($value,"gzip") !== FALSE){
        //Detect gzip encoding
        $accepteh=TRUE;
    }
    else if(stripos($value,$destserver) !== FALSE){
        logger("Fixing ip");
        $value = str_replace($destserver, $lbip, $value);
    }
    logger("returning $value");
    header("$value");
}
logger("trying to swap back username $unm");
$body = str_replace('friendlyName="'.$destname.'"', 'friendlyName="'.$lbname.'"', $body);
$body = str_replace('machineIdentifier="'.$destuuid.'"', 'machineIdentifier="'.$lbuuidkvp[$unm].'"', $body);
$body = str_replace('myPlexUsername="'.$username.'"', 'myPlexUsername="'.$unm.'"', $body);
logger("");
if(($accepteh === TRUE && $acceptr === TRUE)){
    echo gzencode($body);
}
else{
    echo $body;
}
