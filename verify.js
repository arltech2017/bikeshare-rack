#!/usr/bin/env nodejs
var c = require('crypto');
var secret = "ITSAKEY";

codelen = 3

function pad(num, size) {
    var s = num+"";
    while (s.length < size) s = "0" + s;
    return s;
}

function createCode(message) {
	hex = c.createHmac('sha256', secret).update(message).digest('hex')
	code = truncate(hex);
	return code;
}

function truncate(hex) { 
	    //return pad(parseInt(hex.substring(0, 2), 16), 3);
	return pad(parseInt(hex, 16) % (Math.pow(10, codelen)), codelen);
}

var fs =  require('fs');
function countUp() {
	counter = fs.readFileSync('counter.txt', 'utf-8');
	fs.writeFile('counter.txt', (parseInt(counter) + 1).toString());
	return counter
}

console.log("Content-type: plain/text\n");
counter = countUp().trim()
index = "0"
console.log(createCode(counter) + createCode(counter + index))
