// ==UserScript==
// @name Full-browser Video
// @description Loads videos from Twitch and Youtube in 'full-browser', i.e. filling to the edge of the browser, but not fullscreen.
// @match http://www.twitch.tv/*
// @match http://www.youtube.com/*
// @match https://www.youtube.com/*
// @version 2.2
// ==/UserScript==

function redirect(url) {
	document.head.innerHTML += '\n<meta http-equiv="refresh" content="0; url='+url+'">';
}

var path = window.location.pathname.split('/');
var host = window.location.hostname.split('.')[1];
if (path[path.length-1] == '') { // If the url ends with a '/', like twitch.tv/
	path.pop();
}
var query = window.location.search;

if (host == 'twitch') {
	if (path.length == 2) { // Viewing a channel
		redirect('http://player.twitch.tv/?branding=false&showInfo=false&channel='+path[1]);
	} else if (path.length == 4 && path[2] == 'v') { // Viewing a twitch vod
		redirect'http://player.twitch.tv/?branding=false&showInfo=false&video='+path[2]+path[3]);
	}
} else if (host == 'youtube') {
	if (path[1] == 'watch') { // Watching a youtube video
		var parts = query.slice(1).split('&');
		for (var p=0; p<parts.length; p++) {
			if (parts[p].substring(0, 2) == 'v=') {
				redirect('www.youtube.com/embed/'+parts[p].substring(2)+'?'+query.slice(1));
			}
		}
	}
}