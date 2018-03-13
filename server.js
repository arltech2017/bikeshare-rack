console.log("HI");
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

for(i = 0; i < 10; i++) {
    console.log(createCode(counter.toString()));
    counter++;
}
