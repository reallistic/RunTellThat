<?php
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
        logger("Got username $usernm from plex.tv");
        return $usernm;
    }
    else{
        logger("Username tag not found");
        return "";
    }

}

function setupLogging(){
	global $log,$loggingenabled,$maxlogsize, $logdir,$logfilename,$loghistorylength;;
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

function swapBackBody($body){
	global $destname, $lbname, $destuuid, $lbuuidkvp, $username, $token, $utoken, $unm;
	if(strpos($body,'friendlyName="'.$destname.'"') !== FALSE){
	    $body = str_replace('friendlyName="'.$destname.'"', 'friendlyName="'.$lbname.'"', $body);
	    logger("trying to swap back friendlyname from $destname to $lbname");
	}
	if(strpos($body,'machineIdentifier="'.$destuuid.'"') !== FALSE){
	    $body = str_replace('machineIdentifier="'.$destuuid.'"', 'machineIdentifier="'.$lbuuidkvp[urldecode($unm)].'"', $body);
	    logger("trying to swap back machineID from $destuuid to ".$lbuuidkvp[urldecode($unm)]);
	}
	if(strpos($body,'myPlexUsername="'.$username.'"') !== FALSE){
	    $body = str_replace('myPlexUsername="'.$username.'"', 'myPlexUsername="'.$unm.'"', $body);
	    logger("trying to swap back username from $username to $unm");
	}
	if(strpos($body,'username="'.$username.'"') !== FALSE){
	    $body = str_replace('username="'.$username.'"', 'username="'.$unm.'"', $body);
	    logger("trying to swap back username from $username to $unm");
	}
	if(strpos($body,'authToken="'.$token.'"') !== FALSE){
	    $body = str_replace('authToken="'.$token.'"', 'authToken="'.$utoken.'"', $body);
	    logger("trying to swap back token from $token to $utoken");
	}
	return $body;
}

function sendRequest($finalurl, $headers, $method){
	$ch = curl_init($finalurl);
	curl_setopt($ch,CURLOPT_ENCODING, '');
	curl_setopt($ch,CURLOPT_RETURNTRANSFER,true);
	curl_setopt($ch,CURLOPT_VERBOSE,1);
	curl_setopt($ch, CURLOPT_HEADER, true);
	curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
	curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
	return curl_exec($ch);
}

function checkBlockUrls($ouri, $originalurl){
	if( stripos($ouri, "/:/prefs") !== FALSE ||
	    (stripos($ouri, "/:/plugins") !== FALSE && stripos($ouri, "/prefs") !== FALSE) ||
	    stripos($ouri, "/system/appstore") !== FALSE ||
	    stripos($ouri, "/status/sessions") !== FALSE ||
	    ($blocksections === TRUE && stripos($ouri, "/library/") !== FALSE ) ){
	    //block
	       // /:/plugins/<packagename>/prefs
	       // /:/prefs
	       // status/sessions
	       // /library/ IF $blocksections is set
	    //allow
	      //  /video/<channel>
	      //  /music/<channel>
	      //  /photo/<channel>
	    logger("blocking $ouri");
	    header("Location: $originalurl");
	    exit;
	}
}
?>