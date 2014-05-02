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
$utoken = "";
$uhtoken = "";

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
    if(!is_int($maxlogsize)){
        $maxlogsize = 1 * 1024 * 1024; //1MB
    }
    logger("=============================================");
}

function logger($data){
    global $log,$loggingenabled,$maxlogsize;
    if(!$loggingenabled){
        return;
    }
    $today = date("Y-m-d H:i:s");
    file_put_contents($log,"[$today]: $data\r\n",FILE_APPEND);
    if(filesize($log) > $maxlogsize){ //set this in config. Default is 1 MB
        logrotate();
    }
}

function logrotate(){
    global $logdir,$logfilename,$log,$loghistorylength;
    $logfiles = scandir($logdir);
    natsort($logfiles);
    $logfiles = array_reverse($logfiles);
    $postlog=array();
    foreach ($logfiles as $file) {
        if(stripos($file, $logfilename) !== FALSE && $file != $logfilename){
            $clognum = str_replace($logfilename.".","",$file);
            $clognum = intval($clognum);
            $postlog[] = "Current log is $clognum";
            if($clognum >= $loghistorylength){
                unlink("$logdir/$file");
                $postlog[] = "removing log file $logdir/$file";
            }
            elseif($clognum == 0 || $clognum == "0"){
            }
            else{
                rename("$logdir/$file", "$log.".($clognum+1));
                $postlog[]= "renaming log from $logdir/$file to $log.".($clognum+1);
            }
        }
    }
    rename($log, "$log.1");
    touch($log);
    foreach($postlog as $plogl){
        logger($plogl);
    }
}
/*
//In my tests I found that the client identifier doesnt much matter.
//Only the username and token needs to be changed
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
*/

function fixRequestUri($uri){
    global $token, $username, $lbip, $destserver, $unm,$utoken;//, $client
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
                $utoken = $kvp[1];
                logger("found user token $utoken");
                $kvp[1] = $token;
                logger("fixing url part ".$kvp[0]."=".$kvp[1]);
            break;
            case 'X-Plex-Username':
                $unm = $kvp[1];
                logger("found username $unm");
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

function getUsername($userheaders){
    $ch = curl_init("https://plex.tv/users/account");
    curl_setopt($ch,CURLOPT_ENCODING, '');
    curl_setopt($ch,CURLOPT_RETURNTRANSFER,true);
    curl_setopt($ch,CURLOPT_VERBOSE,1);
    curl_setopt($ch, CURLOPT_HEADER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, $userheaders);
    $output = curl_exec($ch);
    curl_close($ch);
    if(strpos($output,"<username>") != FALSE){
        $st = strpos($output,"<username>") + strlen("<username>");
        $ed = strpos($output,"</username>");
        $usernm=substr($output,$st,($ed-$st));
        logger("found username $usernm");
        return $usernm;
    }
    else{
        logger("Username tag not found");
        return "";
    }

}

$headers = array();
$userheaders = array();
$accepteh=FALSE;
$acceptr=FALSE;



//logger($_SERVER['REQUEST_METHOD']);
//logger($_SERVER['REQUEST_URI']);
$ouri = $_SERVER['REQUEST_URI'];
$originalurl = "http://$destserver$ouri";
if( stripos($ouri, "/:/prefs") !== FALSE ||
    (stripos($ouri, "/:/plugins") !== FALSE && stripos($ouri, "/prefs") !== FALSE) ||
    stripos($ouri, "/status/sessions") !== FALSE){
    //block
       // /:/plugins/<packagename>/prefs
       // /:/prefs
       // status/sessions
    //allow
      //  /video/<channel>
      //  /music/<channel>
      //  /photo/<channel>
    logger("blocking $ouri");
    logger("http://$destserver$ouri");
    header("Location: $originalurl");
    exit;
}
$ruri = fixRequestUri($ouri);
$finalurl = "http://$destserver$ruri";
//logger("http://$destserver$ruri");
foreach (getallheaders() as $name => $value) {
    $ovalue = $value;
    switch ($name) {
        case 'X-Plex-Token':
            logger("fixing $name");
            $uhtoken = $value;
            logger("found user token $utoken");
            $value = $token;
            logger("adding $name $value");
        break;
        case 'X-Plex-Username':
            logger("fixing $name");
            $unm = $value;
            logger("found username $unm");
            $value = $username;
            logger("adding $name $value");
        break;
        case 'Referer':
        case 'Host':
        case 'Origin':
            logger("fixing $name");
            $value = str_replace($lbip,$destserver, $value);
            logger("adding $name $value");
        break;
        //With RTT Client you can instead stream media instead of redirecting
        case 'Range':
            if($enablerttclientmode && stripos($finalurl,"/library/parts/") !== FALSE){
                logger("checking range $value");
                $valsplit = explode("-",$value);
                logger("checking range0 ".$valsplit[0]);
                $valsplit[0] = explode("=",$valsplit[0])[1];
                logger("checking range1 ".$valsplit[0]);
                logger("checking range count ".count($valsplit));
                if(count($valsplit) > 1 && intval($valsplit[1])-intval($valsplit[0])>$streamsize){
                    logger('fixing range');
                    $newend=intval($valsplit[0])+$streamsize;
                    $value = "bytes=".$valsplit[0]."-$newend";
                }
                elseif(count($valsplit) == 1 || (count($valsplit) ==2 && $valsplit[1]=="") ){
                    logger('fixing range');
                    $newend=intval($valsplit[0])+$streamsize;
                    $value = "bytes=".$valsplit[0]."-$newend";
                }
                logger("adding $name $value");
            }
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

    $headers[] = "$name: $value";
    $userheaders[] = "$name: $ovalue";
}

//To enable RTT Client mode so that you can instead stream media instead of redirecting
if(!$enablerttclientmode && (stripos($finalurl,"/library/parts/") !== FALSE || stripos($finalurl,"/video/:/transcode/") !== FALSE) ){
    $finalurlre = "http://$destserverre$ruri";
    header("Location: $finalurlre");
    logger("Redirecting to redue load");
    exit;
}

if($unm == "" && ($utoken != "" || $uhtoken != "" ) ){
    if($uhtoken == ""){
       $uhtoken = $utoken;
       $userheaders[] = "X-Plex-Token: $uhtoken";
    }
    elseif($utoken == ""){
       $utoken = $uhtoken;
    }
    logger("looking up username with token $utoken");
    $unm = getUsername($userheaders);
    logger("changing username to $unm");
}

$ch = curl_init($finalurl);
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



//logger($httpCode);
//logger($_SERVER['REQUEST_URI']);
//logger("http://$destserver$ruri");
foreach($header as $value){
    if($firstrun === TRUE){
        //The first header is always HTTP 1/1 CODE
        //Sending this messes things up
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
    header("$value");
}


if(strpos($body,'friendlyName="'.$destname.'"') !== FALSE){
    $body = str_replace('friendlyName="'.$destname.'"', 'friendlyName="'.$lbname.'"', $body);
    logger("trying to swap back friendlyname $lbname");
}
if(strpos($body,'machineIdentifier="'.$destuuid.'"') !== FALSE){
    $body = str_replace('machineIdentifier="'.$destuuid.'"', 'machineIdentifier="'.$lbuuidkvp[$unm].'"', $body);
    logger("trying to swap back machineID ".$lbuuidkvp[$unm]);
}
if(strpos($body,'myPlexUsername="'.$username.'"') !== FALSE){
    $body = str_replace('myPlexUsername="'.$username.'"', 'myPlexUsername="'.$unm.'"', $body);
    logger("trying to swap back username $unm");
}
if(strpos($body,'username="'.$username.'"') !== FALSE){
    $body = str_replace('username="'.$username.'"', 'username="'.$unm.'"', $body);
    logger("trying to swap back username $unm");
}
if(strpos($body,'authToken="'.$token.'"') !== FALSE){
    $body = str_replace('authToken="'.$token.'"', 'authToken="'.$utoken.'"', $body);
    logger("trying to swap back token $utoken");
}

if(($accepteh === TRUE && $acceptr === TRUE)){
    echo gzencode($body);
}
else{
    echo $body;
}

exit;
?>
