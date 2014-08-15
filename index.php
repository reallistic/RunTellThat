<?php
//v1.0
try{
    require 'config.php';
    require 'functions.php';
}
catch (Exception $e){
    error_log ( "Error with PMS Load Balancer in ".__FILE__." at line 3. Unable to get config and/or functions");
    exit;
}

$unm = "";
$utoken = "";
$uhtoken = "";
$logdir = "./";
setupLogging();

$headers = array();
$userheaders = array();
$accepteh=FALSE;
$acceptr=FALSE;

$ouri = $_SERVER['REQUEST_URI'];
$originalurl = "http://$destserver$ouri";

checkBlockUrls($ouri, $originalurl);

$ruri = fixRequestUri($ouri);

$finalurl = "http://$destserver$ruri";
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

if(stripos($finalurl,"/library/parts/") !== FALSE || stripos($finalurl,"/video/:/transcode/") !== FALSE){
    $finalurlre = "http://$destserverre$ruri";
    header("Location: $finalurlre");
    logger("Redirecting to reduce load");
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
}

$output = sendRequest($finalurl, $headers, $_SERVER['REQUEST_METHOD']);

//Get the response code before closing curl
$httpCode = curl_getinfo ( $ch, CURLINFO_HTTP_CODE );
curl_close($ch);

//Split the response to retreive headers
list($header, $body) = explode("\r\n\r\n", $output, 2);
$header = explode("\r\n",$header);

//Send response code
http_response_code(intval($httpCode));
$firstrun = TRUE;

logger("Server response code $httpCode");
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
        logger("Fixing ip from $destserver to $lbip");
        $value = str_replace($destserver, $lbip, $value);
    }
    header("$value");
}

$body = swapBackBody($body);

if(($accepteh === TRUE && $acceptr === TRUE)){
    echo gzencode($body);
}
else{
    echo $body;
}

exit;
?>