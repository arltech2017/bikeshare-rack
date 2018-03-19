#!/usr/bin/env nodejs
var c = require('crypto');
var secret = "ITSAKEY";
var counter = 0;

function createCode(message) {
	    hex = c.createHmac('sha256', secret).update(message).digest('hex');
		code = truncate(hex);
	    return code;
}

function truncate(hex) { 
	    return parseInt(hex.substring(0, 2), 16);
}


var fs =  require('fs');
function countUp() {
	counter = fs.readFileSync('counter.txt', 'utf-8');
	fs.writeFile('counter.txt', (parseInt(counter) + 1).toString());
	return counter
}

console.log("Content-type: plain/text\n");
counter = countUp()
console.log(createCode(counter.trim()))
